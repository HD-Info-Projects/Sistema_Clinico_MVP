import base64
import os
import re
from datetime import date, datetime, time
from decimal import Decimal

from dotenv import load_dotenv
from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.routes.prontuario_route import _referencia_autorizada_paciente
from src.security.decorators import roles_required
from src.security.unidades import unidade_id_request

load_dotenv()

exames_pacs_bp = Blueprint("exames_pacs", __name__, url_prefix="/exames-pacs")
VIEWER_URL_KEYS = ("message", "url", "viewerUrl", "viewer_url", "link", "href")


def _normalizar_valor(valor):
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


def _row_para_dict(row, nomes_colunas):
    return {
        nome: _normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def _texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def _normalizar_int(valor):
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        try:
            return int(float(str(valor).replace(",", ".")))
        except (TypeError, ValueError):
            return None


def _normalizar_bool(valor):
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    if isinstance(valor, (int, float, Decimal)):
        return bool(valor)
    return str(valor).strip().upper() in {"1", "S", "SIM", "TRUE", "T"}


def _normalizar_base64_pdf(valor):
    if valor is None:
        return None

    conteudo = valor.read() if hasattr(valor, "read") else valor
    if isinstance(conteudo, memoryview):
        conteudo = conteudo.tobytes()

    if isinstance(conteudo, bytes):
        if conteudo.startswith(b"%PDF"):
            return base64.b64encode(conteudo).decode("ascii")
        try:
            texto = conteudo.decode("utf-8").strip()
        except UnicodeDecodeError:
            return base64.b64encode(conteudo).decode("ascii")
    else:
        texto = str(conteudo).strip()

    if not texto:
        return None
    if texto.startswith("data:") and "," in texto:
        texto = texto.split(",", 1)[1]
    if texto.startswith("%PDF"):
        return base64.b64encode(texto.encode("latin1", errors="ignore")).decode("ascii")
    return re.sub(r"\s+", "", texto)


def _pacs_config():
    url = os.getenv("URL_EXAMES_PACS")
    token = os.getenv("TOKEN_EXAMES_PACS")

    if not url:
        raise RuntimeError("URL_EXAMES_PACS não configurada")
    if not token:
        raise RuntimeError("TOKEN_EXAMES_PACS não configurado")

    return url, token


def _extrair_viewer_url(payload):
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
        return _extrair_viewer_url(data)

    return None


def _chamar_viewer_exame(id_lancamento: int, timeout=15):
    url, token = _pacs_config()
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
    except ValueError:
        payload = {
            "content_type": response.headers.get("Content-Type"),
            "text": response.text,
        }

    return payload, response.status_code


def _tem_imagem_pacs(id_lancamento: int):
    try:
        payload, _ = _chamar_viewer_exame(id_lancamento, timeout=5)
    except (RuntimeError, requests.RequestException):
        return False

    return bool(_extrair_viewer_url(payload))


def _buscar_exames_paciente_firebird(paciente_id: int):
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
        rows = [_row_para_dict(row, nomes_colunas) for row in cursor.fetchall()]
        cursor.close()

    return rows


def _buscar_paciente_do_lancamento(id_lancamento: int):
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
        result = _row_para_dict(row, nomes_colunas)
        cursor.close()

    return result


def _buscar_laudo_firebird(id_lancamento: int):
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
        laudo = _normalizar_base64_pdf(row[0]) if row else None
        cursor.close()

    return laudo


def _garantir_acesso_paciente(usuario_id: int, paciente_id: int):
    return _referencia_autorizada_paciente(
        usuario_id,
        paciente_id=paciente_id,
        unidade_id=unidade_id_request(),
    )


def _garantir_acesso_lancamento(usuario_id: int, id_lancamento: int):
    referencia = _buscar_paciente_do_lancamento(id_lancamento)
    if not referencia:
        raise LookupError("Exame não encontrado")

    paciente_id = _normalizar_int(referencia.get("ID_PACIENTE_SPDATA"))
    if paciente_id is None:
        raise LookupError("Paciente do exame não encontrado")

    _garantir_acesso_paciente(usuario_id, paciente_id)
    return referencia


def _exame_para_frontend(row):
    id_lancamento = _normalizar_int(row.get("ID_TOKEN_LANCAMENTO_EXAME"))
    nome_exame = _texto(row.get("NOME_EXAME")) or _texto(row.get("EXAME")) or f"Exame {id_lancamento}"
    return {
        "idTokenLancamentoExame": id_lancamento,
        "pacienteId": _normalizar_int(row.get("ID_PACIENTE_SPDATA")),
        "paciente": _texto(row.get("PACIENTE")),
        "prontuario": _texto(row.get("PRONTUARIO")),
        "dataLancamento": row.get("DATA_LANCAMENTO"),
        "dataResultado": row.get("DATA_RESULTADO"),
        "codigoExame": _texto(row.get("EXAME")),
        "sequencia": _normalizar_int(row.get("SEQUENCIA")),
        "ato": _normalizar_int(row.get("ATO")),
        "nomeExame": nome_exame,
        "statusExame": _texto(row.get("STATUS_EXAME")) or "Realizado",
        "temLaudo": _normalizar_bool(row.get("TEM_LAUDO")),
        "temImagem": _tem_imagem_pacs(id_lancamento) if id_lancamento else False,
    }


@exames_pacs_bp.route("/paciente/<int:paciente_id>", methods=["GET"])
@jwt_required()
@roles_required("medico")
def listar_exames_paciente(paciente_id: int):
    try:
        usuario_id = int(get_jwt_identity())
        referencia = _garantir_acesso_paciente(usuario_id, paciente_id)
        paciente_id_autorizado = _normalizar_int(referencia.get("paciente_id")) or paciente_id
        rows = _buscar_exames_paciente_firebird(paciente_id_autorizado)
        return jsonify({
            "pacienteId": paciente_id_autorizado,
            "items": [_exame_para_frontend(row) for row in rows],
        }), 200

    except PermissionError:
        return jsonify({"error": "Paciente não encontrado"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Erro ao listar exames PACS do paciente")
        return jsonify({"error": "Erro interno ao listar exames do paciente"}), 500


@exames_pacs_bp.route("/<int:id>/laudo", methods=["GET"])
@jwt_required()
@roles_required("medico")
def busca_laudo_exame_pacs(id: int):
    try:
        usuario_id = int(get_jwt_identity())
        _garantir_acesso_lancamento(usuario_id, id)
        laudo_base64 = _buscar_laudo_firebird(id)
        if not laudo_base64:
            return jsonify({"error": "Laudo não encontrado"}), 404

        return jsonify({
            "idTokenLancamentoExame": id,
            "contentType": "application/pdf",
            "filename": f"laudo-exame-{id}.pdf",
            "base64": laudo_base64,
        }), 200

    except (LookupError, PermissionError):
        return jsonify({"error": "Exame não encontrado"}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Erro ao buscar laudo PACS do exame")
        return jsonify({"error": "Erro interno ao buscar laudo do exame"}), 500


@exames_pacs_bp.route("/<int:id>", methods=["POST"])
@jwt_required()
@roles_required("medico")
def busca_exames_pacs(id: int):
    try:
        usuario_id = int(get_jwt_identity())
        _garantir_acesso_lancamento(usuario_id, id)
        payload, status_code = _chamar_viewer_exame(id)
        return jsonify(payload), status_code

    except (LookupError, PermissionError):
        return jsonify({"error": "Exame não encontrado"}), 404
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502
    except Exception:
        current_app.logger.exception("Erro ao buscar viewer PACS do exame")
        return jsonify({"error": "Erro interno ao buscar viewer do exame"}), 500
