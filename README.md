# FIAP DevOps Lab App

Aplicação simples para praticar Azure DevOps com Azure Boards, Azure Repos, GitHub, Azure Pipelines e Azure Test Plans.

A aplicação usa apenas Python e biblioteca padrão. Isso reduz problemas em sala, porque não exige instalação de frameworks externos.

## Funcionalidades

- Cadastro de usuários via interface web
- API REST para usuários
- Validação de nome obrigatório
- Validação de e-mail
- Testes automatizados com `unittest`
- Geração de resultado JUnit XML para publicação no Azure Pipelines
- Pipeline YAML com build, testes, publicação de resultados e deploy opcional no Azure App Service

## Executar localmente

```bash
python app.py
```

Acesse:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

## Executar testes automatizados

```bash
python run_tests.py
```

O resultado será gerado em:

```text
test-results/unittest.xml
```

## Endpoints principais

```http
GET  /health
GET  /api/users
POST /api/users
GET  /api/users/{id}
```

Exemplo de criação:

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Ana Souza","email":"ana@example.com"}'
```

## Sugestão de Work Items

- User Story: Como usuário, quero cadastrar meu nome e e-mail para ter acesso ao sistema.
- Task: Criar tela de cadastro.
- Task: Criar endpoint POST /api/users.
- Task: Criar validação de e-mail.
- Bug: Sistema aceita e-mail inválido.
- Test Case: Validar cadastro de usuário com dados válidos.

## Sugestão de Test Plan manual

Plano:

```text
Plano de Testes - Release 1
```

Suite:

```text
Cadastro de Usuário
```

Caso de teste:

```text
CT01 - Validar cadastro de usuário com dados válidos
```

Passos:

| Ação | Resultado esperado |
|---|---|
| Acessar `/` | Tela de cadastro exibida |
| Informar nome válido | Campo aceita o valor |
| Informar e-mail válido | Campo aceita o valor |
| Clicar em Cadastrar | Mensagem de sucesso exibida |
| Verificar tabela | Usuário aparece na lista |

## Pipeline

O arquivo `azure-pipelines.yml` executa:

1. Validação de sintaxe
2. Execução dos testes automatizados
3. Publicação dos resultados de testes em JUnit XML
4. Geração do pacote da aplicação
5. Deploy opcional no Azure App Service

Para habilitar o deploy, altere as variáveis no YAML:

```yaml
azureServiceConnection: 'NOME_DA_SERVICE_CONNECTION'
webAppName: 'NOME_DO_APP_SERVICE'
```

## Deploy local com Docker

```bash
docker build -t fiap-devops-lab-app .
docker run -p 8000:8000 fiap-devops-lab-app
```
