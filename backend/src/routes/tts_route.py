import asyncio
import io
import re

from flask import Blueprint, Response, current_app, jsonify, request

from src.models.auditoria_model import AcaoAuditoria
from src.services.auditoria_service import registrar_auditoria
from src.settings.extensions import limiter


tts_bp = Blueprint("tts", __name__, url_prefix="/tts")

MAX_TTS_TEXT_LENGTH = 240
VOICES = {
    "antonio": "pt-BR-AntonioNeural",
    "francisca": "pt-BR-FranciscaNeural",
}
DEFAULT_VOICE = "antonio"
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CID_PATTERN = re.compile(r"\bCID\s*[-:]?\s*[A-Z][0-9]{2}(?:\.[0-9A-Z]+)?\b", re.IGNORECASE)
TERMOS_CLINICOS_BLOQUEADOS = (
    "diagnóstico",
    "diagnostico",
    "medicamento",
    "prescrição",
    "prescricao",
    "exame",
    "anamnese",
    "prontuário",
    "prontuario",
)


def _tts_rate_limit():
    return current_app.config.get("TTS_RATE_LIMIT", "30 per minute")


def _texto_tts_permitido(texto):
    if CPF_PATTERN.search(texto) or CID_PATTERN.search(texto):
        return False

    texto_normalizado = texto.casefold()
    return not any(termo in texto_normalizado for termo in TERMOS_CLINICOS_BLOQUEADOS)


async def _gerar_audio_edge_tts(texto, voice):
    import edge_tts

    communicate = edge_tts.Communicate(texto, voice)
    buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    return buffer.getvalue()


@tts_bp.route("/speak", methods=["POST"])
@limiter.limit(_tts_rate_limit)
def speak():
    if not current_app.config.get("ENABLE_TTS", False):
        return jsonify({"error": "TTS desabilitado"}), 503

    body = request.get_json(silent=True) or {}
    texto = str(body.get("text") or "").strip()
    voice_key = str(body.get("voice") or DEFAULT_VOICE).strip().casefold()
    chamado_id = body.get("chamadoId") or body.get("chamado_id")

    if not texto:
        return jsonify({"error": "Campo 'text' é obrigatório"}), 400

    if len(texto) > MAX_TTS_TEXT_LENGTH:
        error = f"Campo 'text' deve ter até {MAX_TTS_TEXT_LENGTH} caracteres"
        return (
            jsonify({"error": error}),
            400,
        )

    if not _texto_tts_permitido(texto):
        return jsonify({"error": "Texto não permitido para TTS"}), 400

    voice = VOICES.get(voice_key)
    if not voice:
        return jsonify({"error": "Voz inválida"}), 400

    try:
        audio_bytes = asyncio.run(_gerar_audio_edge_tts(texto, voice))
    except ModuleNotFoundError as e:
        if e.name != "edge_tts":
            raise

        current_app.logger.exception("Dependência edge-tts indisponível")
        return jsonify({"error": "Dependência edge-tts não instalada"}), 500
    except Exception:
        current_app.logger.exception("Falha ao gerar TTS")
        return jsonify({"error": "Erro ao gerar TTS"}), 500

    if not audio_bytes:
        return jsonify({"error": "Nenhum áudio gerado"}), 500

    try:
        entidade_id = int(chamado_id) if chamado_id is not None else None
    except (TypeError, ValueError):
        entidade_id = None

    registrar_auditoria(
        AcaoAuditoria.TTS_SOLICITADO,
        entidade="tts",
        entidade_id=entidade_id,
        descricao=(
            "TTS gerado com sucesso. "
            f"voice={voice_key} tamanho_texto={len(texto)}"
        ),
    )

    return Response(
        audio_bytes,
        mimetype="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-store",
        },
    )
