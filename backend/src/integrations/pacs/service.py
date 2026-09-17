import base64
import os
import re
from datetime import date, datetime, time
from decimal import Decimal

from dotenv import load_dotenv
from flask import current_app, has_app_context
import requests

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.db.handler_redis_db import ConnectionDBRedis

load_dotenv()

VIEWER_URL_KEYS = ("message", "url", "viewerUrl", "viewer_url", "link", "href")
PACS_VIEWER_INTERNAL_ORIGIN_RE = re.compile(
    r"^https://192\.168\.5\.21(?=/|$)",
    flags=re.IGNORECASE,
)
PACS_VIEWER_PUBLIC_ORIGIN = "https://natuslumine.am2saude.com"


def _int_env(nome, default):
    try:
        return int(os.getenv(nome, default))
    except (TypeError, ValueError):
        return default


TEM_IMAGEM_CACHE_TTL_SECONDS = _int_env("PACS_TEM_IMAGEM_CACHE_TTL_SECONDS", 21600)


def normalizar_valor(valor):
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.decode("cp1252", errors="replace")
    return valor


def row_para_dict(row, nomes_colunas):
    return {
        nome: normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def normalizar_int(valor):
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        try:
            return int(float(str(valor).replace(",", ".")))
        except (TypeError, ValueError):
            return None


def normalizar_bool(valor):
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    if isinstance(valor, (int, float, Decimal)):
        return bool(valor)
    return str(valor).strip().upper() in {"1", "S", "SIM", "TRUE", "T"}


def normalizar_base64_pdf(valor):
    if valor is None:
        return None

    conteudo = valor.read() if hasattr(valor, "read") else valor
    if isinstance(conteudo, memoryview):
        conteudo = conteudo.tobytes()

    if isinstance(conteudo, bytes):
        if conteudo.startswith(b"%PDF"):
            return base64.b64encode(conteudo).decode("ascii")
        try:
            texto_pdf = conteudo.decode("utf-8").strip()
        except UnicodeDecodeError:
            return base64.b64encode(conteudo).decode("ascii")
    else:
        texto_pdf = str(conteudo).strip()

    if not texto_pdf:
        return None
    if texto_pdf.startswith("data:") and "," in texto_pdf:
        texto_pdf = texto_pdf.split(",", 1)[1]
    if texto_pdf.startswith("%PDF"):
        return base64.b64encode(texto_pdf.encode("latin1", errors="ignore")).decode("ascii")
    return re.sub(r"\s+", "", texto_pdf)


def pacs_config():
    url = os.getenv("URL_EXAMES_PACS")
    token = os.getenv("TOKEN_EXAMES_PACS")

    if not url:
        raise RuntimeError("URL_EXAMES_PACS não configurada")
    if not token:
        raise RuntimeError("TOKEN_EXAMES_PACS não configurado")

    return url, token


def extrair_viewer_url(payload):
    if not isinstance(payload, dict):
        return None

    for chave in VIEWER_URL_KEYS:
        valor = payload.get(chave)
        if isinstance(valor, str):
            url = valor.strip()
            if re.match(r"^https?://", url, flags=re.IGNORECASE):
                return url

    data = payload.get("data")
    if isinstance(data, dict):
        return extrair_viewer_url(data)

    return None


def reescrever_viewer_url_publica(url):
    url_limpa = url.strip()
    return PACS_VIEWER_INTERNAL_ORIGIN_RE.sub(PACS_VIEWER_PUBLIC_ORIGIN, url_limpa)


def reescrever_viewer_urls_payload(payload):
    if not isinstance(payload, dict):
        return payload

    for chave in VIEWER_URL_KEYS:
        valor = payload.get(chave)
        if isinstance(valor, str):
            payload[chave] = reescrever_viewer_url_publica(valor)

    data = payload.get("data")
    if isinstance(data, dict):
        reescrever_viewer_urls_payload(data)

    return payload


def chamar_viewer_exame(id_lancamento: int, timeout=15):
    url, token = pacs_config()
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"treatmentId": str(id_lancamento)},
        timeout=timeout,
    )
    response.raise_for_status()

    try:
        payload = response.json()
        payload = reescrever_viewer_urls_payload(payload)
    except ValueError:
        payload = {
            "content_type": response.headers.get("Content-Type"),
            "text": response.text,
        }

    return payload, response.status_code


def tem_imagem_cache_key(id_lancamento: int):
    return f"pacs:tem-imagem:{id_lancamento}"


def cache_get_tem_imagem(id_lancamento: int):
    try:
        cached = ConnectionDBRedis().get_cache(tem_imagem_cache_key(id_lancamento))
    except Exception:
        return None

    if cached is None:
        return None
    if str(cached) == "1":
        return True
    if str(cached) == "0":
        return False
    return None


def cache_set_tem_imagem(id_lancamento: int, tem_imagem: bool):
    try:
        ConnectionDBRedis().set_cache(
            tem_imagem_cache_key(id_lancamento),
            "1" if tem_imagem else "0",
            ttl=TEM_IMAGEM_CACHE_TTL_SECONDS,
        )
    except Exception:
        return None

    return None


def log_falha_tem_imagem(id_lancamento: int, exc: Exception):
    if has_app_context():
        current_app.logger.info(
            "Falha ao consultar disponibilidade de imagem PACS para SILANEXA.ID=%s: %s",
            id_lancamento,
            exc,
        )


def tem_imagem_pacs(id_lancamento: int):
    cached = cache_get_tem_imagem(id_lancamento)
    if cached is not None:
        return cached

    try:
        payload, _ = chamar_viewer_exame(id_lancamento, timeout=5)
    except RuntimeError as exc:
        log_falha_tem_imagem(id_lancamento, exc)
        return False
    except requests.RequestException as exc:
        log_falha_tem_imagem(id_lancamento, exc)
        cache_set_tem_imagem(id_lancamento, False)
        return False

    tem_imagem = bool(extrair_viewer_url(payload))
    cache_set_tem_imagem(id_lancamento, tem_imagem)
    return tem_imagem


def buscar_exames_paciente_firebird(paciente_id: int):
    sql = """
        SELECT
            SA.ID AS ID_TOKEN_LANCAMENTO_EXAME,
            COALESCE(PAC_ATEND.ID, PAC_PRONT.ID) AS ID_PACIENTE_SPDATA,
            COALESCE(PAC_ATEND.NOME, PAC_PRONT.NOME, SIC.SEGURADO) AS PACIENTE,
            COALESCE(PAC_ATEND.PRONT, PAC_PRONT.PRONT, SIC.PRONT, SA.PRONT) AS PRONTUARIO,
            SA.DATA AS DATA_LANCAMENTO,
            (
                SELECT FIRST 1 SR.DATARES
                FROM SIRES01 SR
                WHERE SR.ID_SILANEXA = SA.ID
                ORDER BY SR.DATARES DESC, SR.ID DESC
            ) AS DATA_RESULTADO,
            SA.EXAME,
            SA.SEQUENCIA,
            SA.ATO,
            PROC.NOME AS NOME_EXAME,
            ST.NOME AS STATUS_EXAME,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM SIRES01 SR_LAUDO
                    WHERE SR_LAUDO.ID_SILANEXA = SA.ID
                      AND SR_LAUDO.RESULTADO_PDF IS NOT NULL
                ) THEN 1
                ELSE 0
            END AS TEM_LAUDO
        FROM SILANEXA SA
        LEFT JOIN SICADATE SIC
            ON SA.ID_SICADATE = SIC.ID
        LEFT JOIN ATCABECATEND ATD
            ON SIC.ID_ATCABECATEND = ATD.ID
        LEFT JOIN RICADPAC PAC_ATEND
            ON PAC_ATEND.ID = ATD.ID_RICADPAC
        LEFT JOIN RICADPAC PAC_PRONT
            ON PAC_PRONT.PRONT = COALESCE(SIC.PRONT, SA.PRONT)
        LEFT JOIN SITABPRO PROC
            ON PROC.CODALF = SA.EXAME
           AND PROC.ATO = SA.ATO
        LEFT JOIN PRSITEXAME ST
            ON ST.ID = SA.ID_PRSITEXAME
        WHERE COALESCE(PAC_ATEND.ID, PAC_PRONT.ID) = ?
          AND EXISTS (
              SELECT 1
              FROM SIRES01 SR_EXISTE
              WHERE SR_EXISTE.ID_SILANEXA = SA.ID
          )
        ORDER BY SA.DATA DESC, SA.ID DESC;
    """

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, (paciente_id,))
        nomes_colunas = [desc[0].strip().upper() for desc in cursor.description]
        rows = [row_para_dict(row, nomes_colunas) for row in cursor.fetchall()]
        cursor.close()

    return rows


def buscar_paciente_do_lancamento(id_lancamento: int):
    sql = """
        SELECT FIRST 1
            SA.ID AS ID_TOKEN_LANCAMENTO_EXAME,
            COALESCE(PAC_ATEND.ID, PAC_PRONT.ID) AS ID_PACIENTE_SPDATA,
            COALESCE(PAC_ATEND.NOME, PAC_PRONT.NOME, SIC.SEGURADO) AS PACIENTE,
            COALESCE(PAC_ATEND.PRONT, PAC_PRONT.PRONT, SIC.PRONT, SA.PRONT) AS PRONTUARIO
        FROM SILANEXA SA
        LEFT JOIN SICADATE SIC
            ON SA.ID_SICADATE = SIC.ID
        LEFT JOIN ATCABECATEND ATD
            ON SIC.ID_ATCABECATEND = ATD.ID
        LEFT JOIN RICADPAC PAC_ATEND
            ON PAC_ATEND.ID = ATD.ID_RICADPAC
        LEFT JOIN RICADPAC PAC_PRONT
            ON PAC_PRONT.PRONT = COALESCE(SIC.PRONT, SA.PRONT)
        WHERE SA.ID = ?;
    """

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, (id_lancamento,))
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            return None
        nomes_colunas = [desc[0].strip().upper() for desc in cursor.description]
        result = row_para_dict(row, nomes_colunas)
        cursor.close()

    return result


def buscar_laudo_firebird(id_lancamento: int):
    sql = """
        SELECT FIRST 1
            SR.RESULTADO_PDF
        FROM SIRES01 SR
        WHERE SR.ID_SILANEXA = ?
          AND SR.RESULTADO_PDF IS NOT NULL
        ORDER BY SR.DATARES DESC, SR.ID DESC;
    """

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, (id_lancamento,))
        row = cursor.fetchone()
        laudo = normalizar_base64_pdf(row[0]) if row else None
        cursor.close()

    return laudo


def exame_para_frontend(row):
    id_lancamento = normalizar_int(row.get("ID_TOKEN_LANCAMENTO_EXAME"))
    nome_exame = texto(row.get("NOME_EXAME")) or texto(row.get("EXAME")) or f"Exame {id_lancamento}"
    return {
        "idTokenLancamentoExame": id_lancamento,
        "pacienteId": normalizar_int(row.get("ID_PACIENTE_SPDATA")),
        "paciente": texto(row.get("PACIENTE")),
        "prontuario": texto(row.get("PRONTUARIO")),
        "dataLancamento": row.get("DATA_LANCAMENTO"),
        "dataResultado": row.get("DATA_RESULTADO"),
        "codigoExame": texto(row.get("EXAME")),
        "sequencia": normalizar_int(row.get("SEQUENCIA")),
        "ato": normalizar_int(row.get("ATO")),
        "nomeExame": nome_exame,
        "statusExame": texto(row.get("STATUS_EXAME")) or "Realizado",
        "temLaudo": normalizar_bool(row.get("TEM_LAUDO")),
        "temImagem": tem_imagem_pacs(id_lancamento) if id_lancamento else False,
    }


__all__ = [
    "PACS_VIEWER_PUBLIC_ORIGIN",
    "TEM_IMAGEM_CACHE_TTL_SECONDS",
    "VIEWER_URL_KEYS",
    "buscar_exames_paciente_firebird",
    "buscar_laudo_firebird",
    "buscar_paciente_do_lancamento",
    "cache_get_tem_imagem",
    "cache_set_tem_imagem",
    "chamar_viewer_exame",
    "exame_para_frontend",
    "extrair_viewer_url",
    "normalizar_base64_pdf",
    "normalizar_bool",
    "normalizar_int",
    "reescrever_viewer_url_publica",
    "reescrever_viewer_urls_payload",
    "tem_imagem_pacs",
]
