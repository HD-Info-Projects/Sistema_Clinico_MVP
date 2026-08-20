#!/usr/bin/env bash
# Cria um backup MySQL comprimido e criptografado sem persistir SQL em claro.
#
# Uso:
#   scripts/backup_mysql_encrypted.sh
#   ENV_FILE=/caminho/seguro/backup.env scripts/backup_mysql_encrypted.sh
#
# Variaveis obrigatorias no ambiente ou ENV_FILE:
#   BACKUP_AGE_RECIPIENT
#
# Variaveis opcionais:
#   COMPOSE_ENV_FILE      Arquivo .env completo usado pelo Docker Compose.
#   MYSQL_MAINTENANCE_LOCK Arquivo de lock compartilhado com o restore.
#   BACKUP_DIR             Diretorio absoluto de destino. O padrao e
#                          $XDG_STATE_HOME/sistema-clinico-mvp/backups/mysql
#                          ou $HOME/.local/state/sistema-clinico-mvp/backups/mysql.
#   BACKUP_RETENTION_DAYS  Dias de retencao (inteiro positivo; padrao: 30).

set -Eeuo pipefail
IFS=$'\n\t'
umask 077

readonly BACKUP_PREFIX='sistema_clinico_mysql'

die() {
    printf 'Erro: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Uso: backup_mysql_encrypted.sh

Gera um mysqldump consistente pelo servico Compose "mysql", comprime com
gzip, criptografa com age e grava um checksum SHA-256 ao lado do backup.
Nenhum dump SQL em claro e gravado em disco.

Configuracao:
  ENV_FILE                  Arquivo .env (padrao: .env da raiz do projeto)
  COMPOSE_ENV_FILE          .env completo do Compose (padrao: .env da raiz)
  MYSQL_MAINTENANCE_LOCK    Lock compartilhado backup/restore (opcional)
  BACKUP_AGE_RECIPIENT      Destinatario age (obrigatorio)
  BACKUP_DIR                Diretorio absoluto de backups (opcional)
  BACKUP_RETENTION_DAYS     Retencao em dias, inteiro positivo (padrao: 30)
EOF
}

if (( $# > 0 )); then
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
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

    for variable_name in \
        BACKUP_AGE_RECIPIENT \
        BACKUP_DIR BACKUP_RETENTION_DAYS; do
        if [[ -v $variable_name ]]; then
            preset["$variable_name"]=1
        fi
    done

    env_contents=$(<"$env_file")
    while IFS= read -r line || [[ -n $line ]]; do
        ((line_number += 1))
        line=${line%$'\r'}
        [[ $line =~ $assignment_re ]] || continue

        key=${BASH_REMATCH[2]}
        raw=${BASH_REMATCH[3]}
        case "$key" in
            BACKUP_AGE_RECIPIENT|BACKUP_DIR|BACKUP_RETENTION_DAYS)
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
require_command mktemp
require_command find
require_command flock
require_command sync

docker compose version >/dev/null 2>&1 || die "Docker Compose v2 nao esta disponivel."

require_nonempty BACKUP_AGE_RECIPIENT

if [[ -z ${BACKUP_DIR:-} ]]; then
    [[ -n ${HOME:-} || -n ${XDG_STATE_HOME:-} ]] || die "HOME ou XDG_STATE_HOME deve estar definido para o BACKUP_DIR padrao."
    BACKUP_DIR="${XDG_STATE_HOME:-"$HOME/.local/state"}/sistema-clinico-mvp/backups/mysql"
fi
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

[[ $BACKUP_DIR == /* ]] || die "BACKUP_DIR deve ser um caminho absoluto."
[[ $BACKUP_DIR != / ]] || die "BACKUP_DIR nao pode ser o diretorio raiz."
[[ $BACKUP_RETENTION_DAYS =~ ^[1-9][0-9]*$ ]] || die "BACKUP_RETENTION_DAYS deve ser um inteiro positivo."
(( 10#$BACKUP_RETENTION_DAYS <= 3650 )) || die "BACKUP_RETENTION_DAYS nao pode exceder 3650 dias."
retention_minutes=$((10#$BACKUP_RETENTION_DAYS * 24 * 60))

if [[ -e $BACKUP_DIR || -L $BACKUP_DIR ]]; then
    [[ -d $BACKUP_DIR && ! -L $BACKUP_DIR ]] || die "BACKUP_DIR deve ser um diretorio real, nao um link simbolico."
else
    mkdir -p -- "$BACKUP_DIR"
fi
chmod 0700 -- "$BACKUP_DIR"

[[ $MYSQL_MAINTENANCE_LOCK == /* ]] || die "MYSQL_MAINTENANCE_LOCK deve ser absoluto."
exec 9>"$MYSQL_MAINTENANCE_LOCK"
flock -n 9 || die "Ja existe uma operacao de backup ou restore em andamento."
chmod 0600 -- "$MYSQL_MAINTENANCE_LOCK"

timestamp=$(date -u +'%Y%m%dT%H%M%SZ')
backup_name="${BACKUP_PREFIX}_${timestamp}.sql.gz.age"
backup_file="$BACKUP_DIR/$backup_name"
checksum_file="${backup_file}.sha256"

[[ ! -e $backup_file && ! -L $backup_file ]] || die "Ja existe um backup para este instante: $backup_file"
[[ ! -e $checksum_file && ! -L $checksum_file ]] || die "Ja existe um checksum para este instante: $checksum_file"

temp_file=''
checksum_temp=''
published_backup=''
published_checksum=''

cleanup() {
    if [[ -n $temp_file ]]; then
        rm -f -- "$temp_file"
    fi
    if [[ -n $checksum_temp ]]; then
        rm -f -- "$checksum_temp"
    fi
    if [[ -n $published_backup ]]; then
        rm -f -- "$published_backup"
    fi
    if [[ -n $published_checksum ]]; then
        rm -f -- "$published_checksum"
    fi
}

trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

temp_file=$(mktemp --tmpdir="$BACKUP_DIR" ".${backup_name}.tmp.XXXXXX")
checksum_temp=$(mktemp --tmpdir="$BACKUP_DIR" ".${backup_name}.sha256.tmp.XXXXXX")
chmod 0600 -- "$temp_file" "$checksum_temp"

compose=(
    docker compose
    --env-file "$COMPOSE_ENV_FILE"
    --project-directory "$PROJECT_ROOT"
    --file "$COMPOSE_FILE"
)

# shellcheck disable=SC2016 # As variaveis expandem somente no shell do container.
if ! "${compose[@]}" exec -T \
    mysql sh -ceu '
    MYSQL_PWD=$MYSQL_PASSWORD
    export MYSQL_PWD
    exec mysqldump \
        --protocol=TCP \
        --host=127.0.0.1 \
        --user="$MYSQL_USER" \
        --default-character-set=utf8mb4 \
        --single-transaction \
        --quick \
        --skip-lock-tables \
        --routines \
        --triggers \
        --events \
        --hex-blob \
        --no-tablespaces \
        --set-gtid-purged=OFF \
        -- "$MYSQL_DATABASE"
' | gzip --stdout | age --encrypt --recipient "$BACKUP_AGE_RECIPIENT" > "$temp_file"; then
    die "Falha ao gerar, comprimir ou criptografar o backup MySQL."
fi

[[ -s $temp_file ]] || die "O backup criptografado resultou em um arquivo vazio."
chmod 0600 -- "$temp_file"

checksum_output=$(sha256sum -- "$temp_file")
checksum=${checksum_output%% *}
[[ $checksum =~ ^[0-9a-fA-F]{64}$ ]] || die "Nao foi possivel calcular o checksum SHA-256."
printf '%s  %s\n' "$checksum" "$backup_name" > "$checksum_temp"
chmod 0600 -- "$checksum_temp"

mv -- "$temp_file" "$backup_file"
temp_file=''
published_backup=$backup_file
mv -- "$checksum_temp" "$checksum_file"
checksum_temp=''
published_checksum=$checksum_file

(
    cd -- "$BACKUP_DIR"
    sha256sum --check --status -- "${backup_name}.sha256"
) || die "Falha ao validar o checksum do backup publicado."
sync -f -- "$backup_file"
sync -f -- "$checksum_file"
sync -f -- "$BACKUP_DIR"
published_backup=''
published_checksum=''

find "$BACKUP_DIR" \
    -regextype posix-extended \
    -maxdepth 1 \
    -type f \
    -regex ".*/${BACKUP_PREFIX}_[0-9]{8}T[0-9]{6}Z\\.sql\\.gz\\.age" \
    -mmin "+$retention_minutes" \
    -print0 |
while IFS= read -r -d '' expired_backup; do
    rm -f -- "$expired_backup" "${expired_backup}.sha256"
done

trap - EXIT HUP INT TERM
printf 'Backup criptografado criado com sucesso: %s\n' "$backup_file"
printf 'Checksum SHA-256 criado: %s\n' "$checksum_file"
