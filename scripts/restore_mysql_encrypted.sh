#!/usr/bin/env bash
# Restaura um backup .sql.gz.age sem persistir SQL em claro.
#
# Uso interativo:
#   scripts/restore_mysql_encrypted.sh /caminho/backup.sql.gz.age
#
# Uso nao interativo, com confirmacao deliberada:
#   RESTORE_CONFIRM=RESTAURAR scripts/restore_mysql_encrypted.sh /caminho/backup.sql.gz.age
#
# ENV_FILE usa por padrao o .env da raiz. AGE_IDENTITY_FILE e obrigatorio.
# As credenciais MySQL sao lidas somente do ambiente interno do container. O arquivo
# <backup>.sha256 e obrigatorio e validado antes de qualquer alteracao no banco.

set -Eeuo pipefail
IFS=$'\n\t'
umask 077

die() {
    printf 'Erro: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Uso: restore_mysql_encrypted.sh ARQUIVO.sql.gz.age

Valida o checksum quando presente e restaura por pipeline:
  age -d | gzip -dc | docker compose exec -T mysql

Nenhum SQL em claro e gravado em disco.

Configuracao:
  ENV_FILE              Arquivo .env (padrao: .env da raiz do projeto)
  COMPOSE_ENV_FILE      .env completo do Compose (padrao: .env da raiz)
  MYSQL_MAINTENANCE_LOCK Lock compartilhado backup/restore (opcional)
  AGE_IDENTITY_FILE     Arquivo de identidade age legivel (obrigatorio)
  RESTORE_CONFIRM       Use RESTAURAR:NOME_DO_BANCO para confirmar sem prompt
EOF
}

if (( $# == 1 )) && [[ $1 == -h || $1 == --help ]]; then
    usage
    exit 0
fi
if (( $# != 1 )); then
    usage >&2
    exit 2
fi

backup_file=$1
if [[ $backup_file != /* && $backup_file == -* ]]; then
    backup_file="./$backup_file"
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
ENV_FILE=${ENV_FILE:-"$PROJECT_ROOT/.env"}
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
COMPOSE_ENV_FILE=${COMPOSE_ENV_FILE:-"$PROJECT_ROOT/.env"}
MYSQL_MAINTENANCE_LOCK=${MYSQL_MAINTENANCE_LOCK:-"$PROJECT_ROOT/.mysql-maintenance.lock"}

[[ -f "$ENV_FILE" && -r "$ENV_FILE" ]] || die "ENV_FILE inexistente ou sem permissao de leitura: $ENV_FILE"
[[ -f "$COMPOSE_ENV_FILE" && -r "$COMPOSE_ENV_FILE" ]] || die "COMPOSE_ENV_FILE inexistente ou sem permissao de leitura: $COMPOSE_ENV_FILE"
[[ -f "$COMPOSE_FILE" && -r "$COMPOSE_FILE" ]] || die "Arquivo Compose nao encontrado: $COMPOSE_FILE"

trim_whitespace() {
    local value=$1

    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    TRIMMED_VALUE=$value
}

parse_env_value() {
    local raw=$1
    local env_file=$2
    local line_number=$3
    local single_quoted_re="^'([^']*)'[[:space:]]*(#.*)?$"
    local double_quoted_re='^"(([^"\\]|\\.)*)"[[:space:]]*(#.*)?$'
    local inline_comment_re='^(.*[^[:space:]])[[:space:]]+#.*$'
    local value

    trim_whitespace "$raw"
    raw=$TRIMMED_VALUE

    if [[ $raw == \'* ]]; then
        [[ $raw =~ $single_quoted_re ]] || die "Valor .env malformado em $env_file:$line_number"
        value=${BASH_REMATCH[1]}
    elif [[ $raw == \"* ]]; then
        [[ $raw =~ $double_quoted_re ]] || die "Valor .env malformado em $env_file:$line_number"
        value=${BASH_REMATCH[1]}
        value=${value//\\n/$'\n'}
        value=${value//\\r/$'\r'}
        value=${value//\\t/$'\t'}
        value=${value//\\\"/\"}
        value=${value//\\\\/\\}
    else
        if [[ $raw =~ $inline_comment_re ]]; then
            raw=${BASH_REMATCH[1]}
        elif [[ $raw == \#* ]]; then
            raw=''
        fi
        trim_whitespace "$raw"
        value=$TRIMMED_VALUE
    fi

    PARSED_ENV_VALUE=$value
}

load_env_file() {
    local env_file=$1
    local line key raw
    local line_number=0
    local assignment_re='^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$'
    local -A preset=()
    local variable_name
    local env_contents

    if [[ -v AGE_IDENTITY_FILE ]]; then
        preset[AGE_IDENTITY_FILE]=1
    fi

    env_contents=$(<"$env_file")
    while IFS= read -r line || [[ -n $line ]]; do
        ((line_number += 1))
        line=${line%$'\r'}
        [[ $line =~ $assignment_re ]] || continue

        key=${BASH_REMATCH[2]}
        raw=${BASH_REMATCH[3]}
        case "$key" in
            AGE_IDENTITY_FILE)
                ;;
            *)
                continue
                ;;
        esac

        [[ -z ${preset[$key]:-} ]] || continue
        parse_env_value "$raw" "$env_file" "$line_number"
        printf -v "$key" '%s' "$PARSED_ENV_VALUE"
        export "${key?}"
    done <<< "$env_contents"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Comando obrigatorio nao encontrado: $1"
}

require_nonempty() {
    local variable_name=$1

    [[ -n ${!variable_name:-} ]] || die "Variavel obrigatoria ausente: $variable_name"
}

load_env_file "$ENV_FILE"

require_command docker
require_command gzip
require_command age
require_command sha256sum
require_command flock

docker compose version >/dev/null 2>&1 || die "Docker Compose v2 nao esta disponivel."

require_nonempty AGE_IDENTITY_FILE

[[ $backup_file == *.sql.gz.age ]] || die "O arquivo deve ter a extensao .sql.gz.age."
[[ -f $backup_file && -r $backup_file && ! -L $backup_file ]] || die "Backup inexistente, simbolico ou sem permissao de leitura: $backup_file"
[[ -s $backup_file ]] || die "O arquivo de backup esta vazio: $backup_file"
[[ -f $AGE_IDENTITY_FILE && -r $AGE_IDENTITY_FILE && ! -L $AGE_IDENTITY_FILE ]] || die "AGE_IDENTITY_FILE inexistente, simbolico ou sem permissao de leitura."

[[ $MYSQL_MAINTENANCE_LOCK == /* ]] || die "MYSQL_MAINTENANCE_LOCK deve ser absoluto."
exec 9>"$MYSQL_MAINTENANCE_LOCK"
flock -n 9 || die "Ja existe uma operacao de backup ou restore em andamento."
chmod 0600 -- "$MYSQL_MAINTENANCE_LOCK"

checksum_file="${backup_file}.sha256"
if [[ -e $checksum_file || -L $checksum_file ]]; then
    [[ -f $checksum_file && -r $checksum_file && ! -L $checksum_file ]] || die "Checksum existente, mas invalido, simbolico ou sem permissao de leitura."

    checksum_content=$(<"$checksum_file")
    checksum_re='^([0-9a-fA-F]{64})[[:space:]][[:space:]]([^/]+)$'
    [[ $checksum_content =~ $checksum_re ]] || die "Formato de checksum SHA-256 invalido."

    expected_checksum=${BASH_REMATCH[1],,}
    checksum_name=${BASH_REMATCH[2]}
    backup_name=${backup_file##*/}
    [[ $checksum_name == "$backup_name" ]] || die "O checksum nao corresponde ao nome do backup informado."

    checksum_output=$(sha256sum -- "$backup_file")
    actual_checksum=${checksum_output%% *}
    actual_checksum=${actual_checksum,,}
    [[ $actual_checksum == "$expected_checksum" ]] || die "Checksum SHA-256 divergente; restore cancelado."
    printf 'Checksum SHA-256 validado com sucesso.\n'
else
    die "Checksum obrigatorio nao encontrado: $checksum_file"
fi

if ! age --decrypt --identity "$AGE_IDENTITY_FILE" -- "$backup_file" |
    gzip --test; then
    die "Falha na validacao completa da descriptografia ou compactacao; restore cancelado."
fi
printf 'Descriptografia e compactacao validadas antes da escrita no MySQL.\n'

compose=(
    docker compose
    --env-file "$COMPOSE_ENV_FILE"
    --project-directory "$PROJECT_ROOT"
    --file "$COMPOSE_FILE"
)

# shellcheck disable=SC2016 # A variavel expande somente no shell do container.
target_database=$("${compose[@]}" exec -T mysql sh -ceu 'printf "%s" "$MYSQL_DATABASE"')
[[ -n $target_database ]] || die "Nao foi possivel identificar o banco MySQL de destino."
expected_confirmation="RESTAURAR:$target_database"

printf '\nATENCAO: o restore pode substituir dados existentes e nao possui rollback automatico.\n' >&2
printf 'Destino: banco MySQL %s configurado em %s.\n' "$target_database" "$COMPOSE_ENV_FILE" >&2
printf 'Origem: %s\n' "$backup_file" >&2

if [[ ${RESTORE_CONFIRM:-} != "$expected_confirmation" ]]; then
    [[ -t 0 ]] || die "Confirmacao interativa indisponivel. Defina RESTORE_CONFIRM=$expected_confirmation deliberadamente."
    printf 'Digite %s para continuar: ' "$expected_confirmation" >&2
    if ! IFS= read -r confirmation; then
        die "Nao foi possivel ler a confirmacao."
    fi
    [[ $confirmation == "$expected_confirmation" ]] || die "Confirmacao incorreta; restore cancelado."
else
    printf 'Confirmacao nao interativa aceita para o banco %s.\n' "$target_database" >&2
fi

# shellcheck disable=SC2016 # As variaveis expandem somente no shell do container.
if ! age --decrypt --identity "$AGE_IDENTITY_FILE" -- "$backup_file" |
    gzip --decompress --stdout |
    "${compose[@]}" exec -T \
    mysql sh -ceu '
        MYSQL_PWD=$MYSQL_PASSWORD
        export MYSQL_PWD
        exec mysql \
            --protocol=TCP \
            --host=127.0.0.1 \
            --user="$MYSQL_USER" \
            --default-character-set=utf8mb4 \
            --database="$MYSQL_DATABASE"
    '; then
    die "Falha ao descriptografar, descomprimir ou importar o backup; o banco pode ter sido alterado parcialmente."
fi

printf 'Restore MySQL concluido com sucesso a partir do backup criptografado.\n'
