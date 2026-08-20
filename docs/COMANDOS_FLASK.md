# Comandos Flask do Backend

Este documento descreve os comandos CLI registrados pelo backend do Sistema Clinico MVP, os comandos nativos do Flask e as operacoes de migrations.

## 1. Preparacao

Execute os comandos a partir do diretorio `backend`:

```bash
cd backend
source .venv/bin/activate
```

Use preferencialmente `python -m flask`, pois isso garante que o Flask executado pertence ao ambiente virtual ativo:

```bash
python -m flask --app run.py --help
```

Se `FLASK_APP=run.py` estiver definido em `backend/.env`, a opcao `--app run.py` pode ser omitida. Este documento a mantem nos exemplos para tornar os comandos explicitos.

Todos os comandos que acessam o banco local dependem de uma `SQLALCHEMY_DATABASE_URI` valida e das migrations aplicadas:

```bash
python -m flask --app run.py db upgrade
python -m flask --app run.py db current
```

Os comandos de integracao com o SPDATA tambem exigem acesso ao Firebird e as variaveis `FIREBIRD_*` configuradas.

## 2. Ajuda e opcoes globais

Listar todos os comandos disponiveis:

```bash
python -m flask --app run.py --help
```

Consultar as opcoes de um comando especifico:

```bash
python -m flask --app run.py NOME-DO-COMANDO --help
```

Opcoes globais principais:

| Opcao | Finalidade |
|---|---|
| `-A, --app IMPORT` | Indica o modulo, arquivo ou factory da aplicacao. |
| `-e, --env-file FILE` | Carrega outro arquivo de ambiente. |
| `--debug` | Ativa o modo debug. |
| `--no-debug` | Desativa o modo debug. |
| `--version` | Exibe a versao do Flask. |
| `--help` | Exibe a ajuda. |

Exemplo usando um arquivo de ambiente especifico:

```bash
python -m flask --env-file .env --app run.py db current
```

## 3. Resumo dos comandos da aplicacao

| Comando | Finalidade | Bancos envolvidos |
|---|---|---|
| `criar-unidade` | Cria uma unidade local. | MySQL |
| `listar-unidades` | Lista as unidades locais. | MySQL |
| `vincular-unidade-usuario` | Vincula um usuario a uma unidade. | MySQL |
| `registrar-admin` | Cria ou atualiza um administrador. | MySQL |
| `registrar-recepcao` | Cria ou atualiza um usuario de recepcao. | MySQL |
| `registrar-medico-spdata` | Localiza um medico no SPDATA e o registra localmente. | Firebird e MySQL |
| `importar-convenios-spdata` | Importa `TBCONVEN`. | Firebird e MySQL |
| `importar-especialidades-spdata` | Importa `TBESPEC`. | Firebird e MySQL |
| `importar-cids-spdata` | Importa `TBCID10`. | Firebird e MySQL |
| `importar-exames-spdata` | Importa exames da `SITABPRO`. | Firebird e MySQL |
| `importar-procedimentos-spdata` | Importa procedimentos da tabela 98. | Firebird e MySQL |
| `exportar-logos-tiss` | Exporta imagens de `TBTISS.LOGOTIPO`. | Firebird e arquivos locais |

## 4. Usuarios

### 4.1. Registrar administrador

Cria um usuario local com perfil `admin`:

```bash
python -m flask --app run.py registrar-admin
```

Sem opcoes, o comando solicita nome, documento, e-mail e senha de forma interativa.

Opcoes:

| Opcao | Descricao |
|---|---|
| `--nome-completo TEXT` | Nome completo do administrador. |
| `--documento TEXT` | CPF ou CNPJ. |
| `--email TEXT` | E-mail usado no login. |
| `--senha TEXT` | Senha inicial. Prefira informar interativamente. |
| `--atualizar` | Atualiza o usuario encontrado pelo e-mail. |
| `--unidade-id INTEGER` | Vincula uma unidade. Pode ser repetida. |

Exemplo:

```bash
python -m flask --app run.py registrar-admin \
  --nome-completo "Administrador da Silva" \
  --documento "00000000000" \
  --email "adm@example.com" \
  --unidade-id 1
```

O terminal solicitara e confirmara a senha sem exibi-la.

Atualizar um administrador existente:

```bash
python -m flask --app run.py registrar-admin \
  --nome-completo "Administrador da Silva" \
  --documento "00000000000" \
  --email "adm@example.com" \
  --atualizar
```

### 4.2. Registrar recepcao

Cria um usuario local com perfil `recepcao`:

```bash
python -m flask --app run.py registrar-recepcao
```

As opcoes sao equivalentes as de `registrar-admin`:

```text
--nome-completo TEXT
--documento TEXT
--email TEXT
--senha TEXT
--atualizar
--unidade-id INTEGER
```

Exemplo:

```bash
python -m flask --app run.py registrar-recepcao \
  --nome-completo "Recepcao Unidade Centro" \
  --documento "11111111111" \
  --email "recepcao@example.com" \
  --unidade-id 1
```

### 4.3. Registrar medico do SPDATA

Localiza um medico em `TBPROFIS` e cria os registros locais correspondentes:

```bash
python -m flask --app run.py registrar-medico-spdata --spdata-id 123
```

E obrigatorio usar exatamente um destes filtros:

```text
--spdata-id INTEGER
--cpf TEXT
--nome TEXT
```

Outras opcoes:

| Opcao | Descricao |
|---|---|
| `--email TEXT` | Define o e-mail local. Se omitido, tenta usar o e-mail do SPDATA. |
| `--crm-atendimento-spdata TEXT` | Sobrescreve `TBCBOPRO.COD` para o filtro da agenda. |
| `--senha TEXT` | Senha inicial. Prefira informar interativamente. |
| `--unidade-id INTEGER` | Vincula uma unidade. Pode ser repetida. |

Exemplos de busca:

```bash
python -m flask --app run.py registrar-medico-spdata --cpf "00000000000"
```

```bash
python -m flask --app run.py registrar-medico-spdata \
  --nome "Maria Silva" \
  --email "maria.silva@example.com" \
  --unidade-id 1
```

## 5. Unidades

### 5.1. Criar unidade

Modo interativo:

```bash
python -m flask --app run.py criar-unidade
```

Opcoes:

| Opcao | Descricao |
|---|---|
| `--nome TEXT` | Nome exibido no sistema. |
| `--slug TEXT` | Identificador publico. Se omitido, e gerado pelo nome. |
| `--codigo-spdata-centro-custo INTEGER` | Codigo `ATCABECATEND.ID_TBCENCUS`. |
| `--codigo-spdata-agenda TEXT` | Codigo `REPACAGD.UNIDADE`. |
| `--endereco TEXT` | Endereco da unidade. |
| `--telefone TEXT` | Telefone da unidade. |

Exemplo:

```bash
python -m flask --app run.py criar-unidade \
  --nome "Unidade Centro" \
  --slug "unidade-centro" \
  --codigo-spdata-centro-custo 1 \
  --codigo-spdata-agenda "CENTRO" \
  --endereco "Rua Exemplo, 100" \
  --telefone "(00) 0000-0000"
```

### 5.2. Listar unidades

```bash
python -m flask --app run.py listar-unidades
```

O resultado apresenta o ID local, nome, status e codigos de integracao de cada unidade.

### 5.3. Vincular usuario a unidade

```bash
python -m flask --app run.py vincular-unidade-usuario \
  --email "adm@example.com" \
  --unidade-id 1 \
  --principal
```

Opcoes:

| Opcao | Obrigatoria | Descricao |
|---|---|---|
| `--email TEXT` | Sim | E-mail do usuario local. |
| `--unidade-id INTEGER` | Sim | ID local da unidade. |
| `--principal` | Nao | Define a unidade como principal para o usuario. |

## 6. Importacoes SPDATA

As importacoes leem o Firebird do SPDATA e gravam espelhos no MySQL local. Antes de executa-las, valide as duas conexoes:

```bash
python -m src.models.db.handler_fb_db
python -m flask --app run.py db current
```

### 6.1. Convenios

Importa `TBCONVEN` para `MED_SPDATA_CONVENIOS`:

```bash
python -m flask --app run.py importar-convenios-spdata
```

Com tamanho de lote personalizado:

```bash
python -m flask --app run.py importar-convenios-spdata --batch-size 500
```

### 6.2. Especialidades

Importa `TBESPEC` para `MED_SPDATA_ESPECIALIDADES`:

```bash
python -m flask --app run.py importar-especialidades-spdata
```

```bash
python -m flask --app run.py importar-especialidades-spdata --batch-size 500
```

### 6.3. CIDs

Importa `TBCID10` para `MED_SPDATA_CIDS`. A busca de CID do prontuario usa este espelho local; por isso, execute este comando depois das migrations e antes de liberar a busca em uma instalacao nova:

```bash
python -m flask --app run.py importar-cids-spdata
```

```bash
python -m flask --app run.py importar-cids-spdata --batch-size 500
```

O comando atualiza codigo e descricao dos CIDs existentes, cria os ausentes e preserva registros locais que nao venham mais do SPDATA.

### 6.4. Exames

Importa exames da `SITABPRO` para o banco local:

```bash
python -m flask --app run.py importar-exames-spdata
```

```bash
python -m flask --app run.py importar-exames-spdata --batch-size 500
```

### 6.5. Procedimentos

Importa procedimentos da tabela 98 do SPDATA:

```bash
python -m flask --app run.py importar-procedimentos-spdata
```

```bash
python -m flask --app run.py importar-procedimentos-spdata --batch-size 500
```

Em todos esses comandos, `--batch-size` aceita um inteiro maior ou igual a 1 e possui valor padrao `200`.

### 6.6. Exportar logos TISS

Exporta `TBTISS.LOGOTIPO` para arquivos estaticos do frontend:

```bash
python -m flask --app run.py exportar-logos-tiss
```

Por padrao, os arquivos sao gravados em `frontend/public/img/convenios`. Para escolher outro diretorio:

```bash
python -m flask --app run.py exportar-logos-tiss \
  --output-dir ../frontend/public/img/convenios
```

## 7. Migrations

Listar os subcomandos do Flask-Migrate:

```bash
python -m flask --app run.py db --help
```

| Comando | Finalidade |
|---|---|
| `db current` | Mostra a revisao aplicada no banco. |
| `db heads` | Mostra as revisoes finais disponiveis no codigo. |
| `db history` | Exibe o historico de revisions. |
| `db show REVISAO` | Exibe os detalhes de uma revision. |
| `db branches` | Exibe pontos de ramificacao. |
| `db check` | Verifica se os models possuem mudancas ainda nao migradas. |
| `db upgrade [REVISAO]` | Aplica migrations ate a revisao informada ou ate `head`. |
| `db downgrade REVISAO` | Reverte ate uma revisao anterior. |
| `db migrate -m "mensagem"` | Gera uma revision por comparacao com os models. |
| `db revision -m "mensagem"` | Cria uma revision manual. |
| `db merge REVISOES` | Cria uma revision para unir multiplos heads. |
| `db stamp REVISAO` | Marca uma revisao sem executar seu SQL. |
| `db edit REVISAO` | Abre uma revision para edicao. |
| `db init` | Cria um repositorio novo de migrations. |
| `db list-templates` | Lista templates de repositorio. |

Aplicar todas as migrations pendentes:

```bash
python -m flask --app run.py db upgrade
```

Conferir se o banco chegou ao head:

```bash
python -m flask --app run.py db current
python -m flask --app run.py db heads
```

Depois de alterar um model:

```bash
python -m flask --app run.py db migrate -m "adiciona campo exemplo"
```

Revise o arquivo gerado em `migrations/versions/` antes de aplicar:

```bash
python -m flask --app run.py db upgrade
```

Cuidados:

- Nao execute `db init` neste projeto; o diretorio `migrations/` ja existe.
- Nao use `db stamp` para corrigir um banco sem confirmar que o schema ja corresponde a revision.
- `db downgrade` pode remover colunas, tabelas e dados.
- Faca backup antes de aplicar migrations em bancos com dados importantes.
- Nunca apague o volume MySQL para tentar corrigir uma migration sem confirmar que os dados podem ser descartados.

## 8. Comandos nativos do Flask

### 8.1. Iniciar servidor de desenvolvimento

```bash
python -m flask --app run.py run --debug
```

Expor em todas as interfaces na porta 5000:

```bash
python -m flask --app run.py run \
  --debug \
  --host 0.0.0.0 \
  --port 5000
```

Opcoes principais:

```text
--debug / --no-debug
--host TEXT
--port INTEGER
--reload / --no-reload
--debugger / --no-debugger
--with-threads / --without-threads
--cert PATH
--key FILE
```

O servidor do Flask e destinado apenas ao desenvolvimento. Em producao, o projeto utiliza Gunicorn.

### 8.2. Listar rotas

```bash
python -m flask --app run.py routes
```

Ordenar por URL:

```bash
python -m flask --app run.py routes --sort rule
```

Exibir tambem `HEAD` e `OPTIONS`:

```bash
python -m flask --app run.py routes --all-methods
```

Valores aceitos por `--sort`:

```text
endpoint
methods
domain
rule
match
```

### 8.3. Shell da aplicacao

```bash
python -m flask --app run.py shell
```

O shell executa com o contexto Flask carregado. Exemplo de consulta:

```python
from src.models.usuario_model import Usuario
Usuario.query.count()
```

## 9. Flask-Limiter

Listar os subcomandos:

```bash
python -m flask --app run.py limiter --help
```

Na instalacao atual, os nomes dos subcomandos sao registrados, mas sua execucao exige o extra de CLI do Flask-Limiter. Sem ele, o Flask exibe `Missing dependencies for flask-limiter cli`.

Instalar o extra no ambiente virtual, se essas operacoes administrativas forem necessarias:

```bash
python -m pip install "flask-limiter[cli]==4.1.1"
```

Exibir a configuracao efetiva:

```bash
python -m flask --app run.py limiter config
```

Listar os limites das rotas:

```bash
python -m flask --app run.py limiter limits
```

Limpar limites de uma chave exige as opcoes indicadas pela versao instalada:

```bash
python -m flask --app run.py limiter clear --help
```

## 10. Diagnostico de erros comuns

### 10.1. MySQL `1045 Access denied`

Exemplo:

```text
Access denied for user 'clinico'@'localhost' (using password: YES)
```

Esse erro significa que o MySQL foi encontrado, mas recusou usuario ou senha. Ele nao e um erro do comando `registrar-admin`.

Confirme, sem imprimir a senha, qual URI a aplicacao carregou:

```bash
python -c "from sqlalchemy.engine import make_url; from src.settings.config import Config; u=make_url(Config.SQLALCHEMY_DATABASE_URI); print(u.drivername, u.host, u.port, u.database, u.username)"
```

Verifique:

- se `backend/.env` aponta para o MySQL correto;
- se usuario, senha e banco coincidem com as variaveis `MYSQL_*` usadas na primeira criacao do container;
- se outro MySQL local esta ocupando a porta `3306`;
- se o volume Docker ja existia antes da alteracao das credenciais.

Importante: alterar `MYSQL_USER` ou `MYSQL_PASSWORD` no `.env` da raiz nao altera automaticamente usuarios de um volume MySQL ja inicializado. Nesse caso, ajuste o usuario no proprio MySQL ou use as credenciais com as quais o volume foi criado. Nao execute `docker compose down -v` se houver dados que precisam ser preservados.

Teste a conexao antes de repetir comandos de cadastro:

```bash
python -m flask --app run.py db current
```

### 10.2. `SQLALCHEMY_DATABASE_URI` ausente

Erro:

```text
Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set.
```

Crie `backend/.env` com base em `backend/.env.example` e configure uma URI valida:

```env
SQLALCHEMY_DATABASE_URI=mysql+pymysql://usuario:senha@127.0.0.1:3306/sistema_clinico_mvp
```

Caracteres especiais da senha precisam estar codificados para URL dentro da URI.

### 10.3. Cliente Firebird nao localizado

Erro:

```text
The location of Firebird Client Library could not be determined.
```

No Ubuntu, instale o cliente nativo:

```bash
sudo apt update
sudo apt install --no-install-recommends libfbclient2
```

Valide:

```bash
python -c "from ctypes.util import find_library; print(find_library('fbclient'))"
python -m src.models.db.handler_fb_db
```

### 10.4. Driver ODBC nao localizado

Erros relacionados a `libodbc.so.2` ou ao `ODBC Driver 18 for SQL Server` indicam que as dependencias nativas do SQL Server nao estao instaladas. O host precisa de unixODBC e do Microsoft ODBC Driver 18; instalar apenas `pyodbc` com `pip` nao e suficiente.

Valide os drivers registrados:

```bash
python -c "import pyodbc; print(pyodbc.drivers())"
```

## 11. Sequencia inicial recomendada

Para preparar uma instalacao nova:

```bash
# Na raiz do projeto
docker compose up -d --wait mysql

# No diretorio backend
source .venv/bin/activate
python -m flask --app run.py db upgrade
python -m flask --app run.py db current
python -m flask --app run.py criar-unidade
python -m flask --app run.py registrar-admin
python -m flask --app run.py listar-unidades
python -m flask --app run.py run --debug
```

Se a integracao SPDATA estiver configurada:

```bash
python -m src.models.db.handler_fb_db
python -m flask --app run.py importar-convenios-spdata
python -m flask --app run.py importar-especialidades-spdata
python -m flask --app run.py importar-cids-spdata
python -m flask --app run.py importar-exames-spdata
python -m flask --app run.py importar-procedimentos-spdata
```
