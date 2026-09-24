import os
import tempfile
import unittest
from pathlib import Path

import app


class UserRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        app.DB_PATH = str(Path(self.tmpdir.name) / "test.db")
        app.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_health_contract(self):
        self.assertEqual("fiap-devops-lab", "fiap-devops-lab")

    def test_create_user_success(self):
        ok, user = app.create_user("Ana Souza", "ana@example.com")
        self.assertTrue(ok)
        self.assertEqual(user["name"], "Ana Souza")
        self.assertEqual(user["email"], "ana@example.com")
        self.assertGreater(user["id"], 0)

    def test_create_user_requires_name(self):
        ok, result = app.create_user("", "ana@example.com")
        self.assertFalse(ok)
        self.assertEqual(result["error"], "Nome é obrigatório")

    def test_create_user_rejects_invalid_email(self):
        ok, result = app.create_user("Ana", "email-invalido")
        self.assertFalse(ok)
        self.assertEqual(result["error"], "E-mail inválido")

    def test_list_users_after_create(self):
        app.create_user("Bruno Lima", "bruno@example.com")
        users = app.list_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["email"], "bruno@example.com")

    def test_duplicate_email_is_rejected(self):
        first_ok, _ = app.create_user("Carla Dias", "carla@example.com")
        second_ok, result = app.create_user("Carla Dias", "carla@example.com")
        self.assertTrue(first_ok)
        self.assertFalse(second_ok)
        self.assertEqual(result["error"], "E-mail já cadastrado")


if __name__ == "__main__":
    unittest.main(verbosity=2)
