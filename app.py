import html
import json
import os
import re
import sqlite3
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DB_PATH = os.getenv("DATABASE", str(Path(tempfile.gettempdir()) / "fiap_devops_lab.db"))
APP_PORT = int(os.getenv("PORT", "8000"))


def get_connection():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
            """
        )
        conn.commit()


def row_to_dict(row):
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def list_users():
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, email FROM users ORDER BY id ASC").fetchall()
    return [row_to_dict(row) for row in rows]


def get_user(user_id):
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row) if row else None

def create_user(name, email):
    init_db()
    name = (name or "").strip()
    email = (email or "").strip().lower()
    if not name:
        return False, {"error": "Nome é obrigatório"}
    if not EMAIL_RE.match(email):
        return False, {"error": "E-mail inválido"}
    try:
        with get_connection() as conn:
            cur = conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
            conn.commit()
            return True, {"id": cur.lastrowid, "name": name, "email": email}
    except sqlite3.IntegrityError:
        return False, {"error": "E-mail já cadastrado"}


def render_home(success=None, error=None):
    users = list_users()
    rows = "".join(
        f"<tr><td>{user['id']}</td><td>{html.escape(user['name'])}</td><td>{html.escape(user['email'])}</td></tr>"
        for user in users
    )
    table = (
        f"<table><thead><tr><th>ID</th><th>Nome</th><th>E-mail</th></tr></thead><tbody>{rows}</tbody></table>"
        if rows
        else '<p class="empty">Nenhum usuário cadastrado ainda.</p>'
    )
    success_block = f'<div class="alert success">{html.escape(success)}</div>' if success else ""
    error_block = f'<div class="alert error">{html.escape(error)}</div>' if error else ""
    return f"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FIAP DevOps Lab</title>
  <link rel="stylesheet" href="/static/app.css">
</head>
<body>
  <main class="container">
    <section class="hero">
      <p class="eyebrow">Azure DevOps • Boards • Repos • Pipelines • Test Plans</p>
      <h1>Cadastro de Usuários</h1>
      <p>Aplicação simples para praticar backlog, commits, pull requests, pipelines, testes manuais e testes automatizados.</p>
    </section>
    {success_block}
    {error_block}
    <section class="card">
      <h2>Novo usuário</h2>
      <form method="post" action="/users" class="form">
        <label>Nome
          <input name="name" placeholder="Ex.: Ana Souza" required>
        </label>
        <label>E-mail
          <input name="email" type="email" placeholder="ana@exemplo.com" required>
        </label>
        <button type="submit">Cadastrar</button>
      </form>
    </section>
    <section class="card">
      <h2>Usuários cadastrados</h2>
      {table}
    </section>
  </main>
</body>
</html>"""


class AppHandler(BaseHTTPRequestHandler):
    server_version = "FIAPDevOpsLab/1.0"

    def _send(self, status, body, content_type="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, payload):
        self._send(status, json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8")

    def _redirect(self, location):
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/":
            self._send(HTTPStatus.OK, render_home(success=query.get("success", [None])[0], error=query.get("error", [None])[0]))
            return
        if path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok", "service": "fiap-devops-lab"})
            return
        if path == "/api/users":
            self._json(HTTPStatus.OK, list_users())
            return
        if path.startswith("/api/users/"):
            try:
                user_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "ID inválido"})
                return
            user = get_user(user_id)
            self._json(HTTPStatus.OK, user) if user else self._json(HTTPStatus.NOT_FOUND, {"error": "Usuário não encontrado"})
            return
        if path == "/static/app.css":
            css_path = Path(__file__).parent / "static" / "app.css"
            self._send(HTTPStatus.OK, css_path.read_text(encoding="utf-8"), "text/css; charset=utf-8")
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada"})

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8")
        if parsed.path == "/users":
            form = parse_qs(raw_body)
            ok, result = create_user(form.get("name", [""])[0], form.get("email", [""])[0])
            if ok:
                self._redirect(f"/?success={html.escape(result['name'])}%20cadastrado%20com%20sucesso")
            else:
                self._redirect(f"/?error={html.escape(result['error'])}")
            return
        if parsed.path == "/api/users":
            try:
                payload = json.loads(raw_body or "{}")
            except json.JSONDecodeError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON inválido"})
                return
            ok, result = create_user(payload.get("name"), payload.get("email"))
            self._json(HTTPStatus.CREATED if ok else HTTPStatus.BAD_REQUEST, result)
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada"})

    def log_message(self, fmt, *args):
        if os.getenv("APP_VERBOSE", "false").lower() == "true":
            super().log_message(fmt, *args)


def run(host="0.0.0.0", port=APP_PORT):
    init_db()
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"FIAP DevOps Lab App executando em http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
