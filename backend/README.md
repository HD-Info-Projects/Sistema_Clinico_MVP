# Backend

API Flask do Sistema Clinico MVP.

## Desenvolvimento local

O fluxo abaixo executa o backend no host e o MySQL no Docker.

1. Crie o `.env` na raiz do projeto com base no `.env.example` e defina as variaveis `MYSQL_*`.
2. Crie `backend/.env` com base em `backend/.env.example`, usando as mesmas credenciais do MySQL.
3. Na raiz do projeto, inicie o banco:

```bash
docker compose up -d --wait mysql
```

4. No diretorio `backend`, ative o ambiente e aplique as migrations existentes:

```bash
source .venv/bin/activate
python -m flask --app run.py db upgrade
python -m flask --app run.py db current
```

Nao execute `flask db init`: o repositorio ja possui o diretorio `migrations/` versionado.

5. Inicie a API:

```bash
python run.py
```

A API fica disponivel em `http://127.0.0.1:5000`.

## Logs operacionais

O backend gera logs em stdout/stderr para uso com Docker e Gunicorn. As principais variaveis sao:

```env
LOG_LEVEL=INFO
LOG_FORMAT=text
LOG_REQUESTS=true
LOG_HEALTHCHECKS=false
```

Cada resposta recebe `X-Request-ID`. Envie esse header a partir do cliente para correlacionar erros entre frontend, backend e logs do container. Logs tecnicos nao devem incluir senhas, tokens, cookies, CPF/CNPJ, telefones, payloads clinicos completos ou credenciais de integracao.
