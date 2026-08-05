# Guia de Deploy Docker na VPS

Este guia mostra como subir o Sistema Clinico MVP em uma VPS usando Docker Compose.

## Arquitetura

O deploy usa cinco containers:

- `caddy`: proxy reverso publico com HTTPS automatico.
- `frontend`: aplicacao Nuxt acessivel publicamente apenas pelo Caddy.
- `backend`: API Flask rodando com Gunicorn, acessivel apenas pela rede interna Docker.
- `mysql`: banco MySQL persistido em volume Docker.
- `redis`: cache Redis persistido em volume Docker.

O Firebird/SPDATA fica fora do Docker e deve estar acessivel pela VPS via rede.

## Arquivos adicionados

- `docker-compose.yml`: orquestra todos os servicos.
- `Caddyfile`: configura o proxy reverso HTTPS para o frontend.
- `.env.example`: modelo das variaveis de producao.
- `backend/Dockerfile`: imagem do Flask/Gunicorn.
- `backend/.dockerignore`: evita copiar arquivos locais para a imagem.
- `frontend/Dockerfile`: imagem do Nuxt em producao.
- `frontend/.dockerignore`: evita copiar `node_modules`, builds locais e `.env`.

Observacao: o container `backend` executa `flask db upgrade` automaticamente antes de iniciar o Gunicorn. Assim, novas migrations sao aplicadas no start do backend durante o deploy.

## Antes de publicar

1. Remova credenciais reais do repositorio.
2. Nao versione arquivos `.env`.
3. Troque senhas que ja tenham sido compartilhadas ou commitadas.
4. Confirme que a VPS consegue acessar o servidor Firebird/SPDATA.
5. Confirme que as portas `80` e `443` da VPS estao liberadas.
6. Aponte o dominio/subdominio para o IP publico da VPS antes de subir o Caddy.

Importante: existe um arquivo local chamado `VPS - Acesso.md` com credenciais. Remova esse arquivo do repositorio e troque a senha da VPS antes de usar em producao.

## Instalar Docker na VPS

Os comandos abaixo consideram uma VPS Ubuntu/Debian com acesso root.

```bash
apt update
apt install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker --version
docker compose version
```

Se a VPS for Debian e o repositorio acima falhar, use o instalador oficial simplificado:

```bash
curl -fsSL https://get.docker.com | sh
docker --version
docker compose version
```

## Enviar o projeto para a VPS

Use Git ou copie o projeto para a VPS. Exemplo usando Git:

```bash
cd /opt
git clone URL_DO_SEU_REPOSITORIO sistema-clinico-mvp
cd sistema-clinico-mvp
```

Se o projeto ja existir na VPS:

```bash
cd /opt/sistema-clinico-mvp
git pull
```

## Configurar variaveis de ambiente

Crie o arquivo `.env` na raiz do projeto a partir do exemplo:

```bash
cp .env.example .env
nano .env
```

Preencha as variaveis:

```env
APP_DOMAIN=sistema.seudominio.com.br
NUXT_ENABLE_MOCK_AUTH=false
NUXT_AUTH_COOKIE_SECURE=true
TZ=America/Sao_Paulo
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120

MYSQL_DATABASE=sistema_clinico_mvp
MYSQL_USER=clinico
MYSQL_PASSWORD=senha_forte_do_mysql
MYSQL_ROOT_PASSWORD=senha_forte_do_root_mysql

SECRET_KEY=senha_forte_para_flask
JWT_SECRET_KEY=senha_forte_para_jwt

FIREBIRD_HOST=ip_ou_host_do_firebird
FIREBIRD_PORT=3050
FIREBIRD_DATABASE=/caminho/para/o/banco.fdb
FIREBIRD_USER=usuario_firebird
FIREBIRD_PASSWORD=senha_firebird
FIREBIRD_CHARSET=WIN1252
```

Observacoes:

- `MYSQL_DATABASE`, `MYSQL_USER` e `MYSQL_PASSWORD` sao usados pelo Flask via `SQLALCHEMY_DATABASE_URI`.
- `NUXT_FLASK_BASE_URL` ja e definido no `docker-compose.yml` como `http://backend:5000`.
- `NUXT_ENABLE_MOCK_AUTH=false` impede login mockado em producao.
- `NUXT_AUTH_COOKIE_SECURE=true` faz o cookie de autenticacao funcionar apenas em HTTPS.
- `APP_DOMAIN` deve ser somente o dominio/subdominio, sem `http://` ou `https://`.
- `TZ=America/Sao_Paulo` mantem backend, frontend e MySQL no fuso esperado.
- `GUNICORN_WORKERS` e `GUNICORN_TIMEOUT` controlam o Gunicorn do backend sem rebuild da imagem.
- `FIREBIRD_HOST` nao pode ser `localhost`, porque dentro do container `localhost` aponta para o proprio container.

## Subir a aplicacao

Antes de subir, confirme que o DNS do dominio ja aponta para a VPS e que as portas `80` e `443` estao liberadas.

Na raiz do projeto, execute:

```bash
docker compose up -d --build
```

Durante esse processo, o backend aplica as migrations do Flask automaticamente antes de iniciar a API.

Confira se os containers subiram:

```bash
docker compose ps
```

O servico `caddy` deve aparecer como `Up`. Os servicos `mysql`, `redis`, `backend` e `frontend` devem aparecer como `healthy` apos alguns segundos.

Se o backend nao ficar `healthy`, verifique os logs. Uma falha de migration impede o Gunicorn de iniciar.

Veja os logs se precisar diagnosticar:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f caddy
docker compose logs -f mysql
```

Depois disso, acesse:

```text
https://APP_DOMAIN
```

Exemplo:

```text
https://sistema.seudominio.com.br
```

## Liberar firewall

Se estiver usando `ufw`:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw enable
ufw status
```

O frontend, backend, MySQL e Redis nao precisam ser expostos publicamente. O acesso publico fica apenas no Caddy.

## Atualizar o deploy

Quando houver novas alteracoes no repositorio:

```bash
cd /opt/sistema-clinico-mvp
git pull
docker compose up -d --build
docker image prune -f
```

As migrations tambem sao executadas automaticamente nesse fluxo, porque o container `backend` roda `flask db upgrade` a cada start.

## Parar e reiniciar

Parar todos os containers:

```bash
docker compose down
```

Reiniciar:

```bash
docker compose up -d
```

Reiniciar apenas um servico:

```bash
docker compose restart caddy
docker compose restart backend
docker compose restart frontend
```

## Backup do MySQL

Gerar backup:

```bash
docker compose exec mysql sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > backup_mysql.sql
```

Restaurar backup:

```bash
docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' < backup_mysql.sql
```

## Diagnostico rapido

Ver status:

```bash
docker compose ps
```

Ver logs do backend:

```bash
docker compose logs --tail=200 backend
```

Ver logs do Caddy e emissao do certificado HTTPS:

```bash
docker compose logs --tail=200 caddy
```

Verificar a revisao atual das migrations, se o backend estiver rodando:

```bash
docker compose exec backend flask db current
```

Rodar migrations manualmente, apenas para diagnostico ou recuperacao:

```bash
docker compose run --rm backend flask db upgrade
```

Entrar no container do backend:

```bash
docker compose exec backend sh
```

Testar conexao Flask internamente:

```bash
docker compose exec frontend wget -qO- http://backend:5000/
```

Testar MySQL internamente:

```bash
docker compose exec mysql sh -c 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD"'
```

Se o build do frontend falhar por falta de memoria, confirme que o `frontend/Dockerfile` contem `NODE_OPTIONS=--max-old-space-size=4096`. Em VPS muito pequenas, aumente a memoria/swap antes de executar `docker compose up -d --build`.

## Observacoes sobre dominio e HTTPS

Este Compose expoe apenas o Caddy nas portas `80` e `443`. O Caddy gera e renova automaticamente o certificado HTTPS do dominio definido em `APP_DOMAIN` e encaminha as requisicoes para o container `frontend:3000`.

Antes de subir o deploy, o DNS do dominio precisa apontar para o IP publico da VPS. Se o DNS ainda nao estiver propagado, o Caddy nao conseguira emitir o certificado.

## Checklist final

- `.env` criado na VPS com senhas fortes.
- `APP_DOMAIN` apontando para o dominio real, sem `http://` ou `https://`.
- Senha da VPS rotacionada caso tenha sido compartilhada.
- `VPS - Acesso.md` removido do repositorio.
- Firebird/SPDATA acessivel a partir da VPS.
- Portas `80` e `443` liberadas.
- `docker compose up -d --build` executado com sucesso.
- Backend ficou `healthy`, indicando que as migrations automaticas passaram e a API iniciou.
- Aplicacao acessivel pelo navegador em HTTPS.
