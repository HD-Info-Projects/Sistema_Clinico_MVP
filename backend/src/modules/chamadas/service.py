import asyncio
import io
import re

from flask import current_app

from src.models.auditoria_model import AcaoAuditoria
from src.services.auditoria_service import registrar_auditoria


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


def _entidade_id_chamado(chamado_id):
    try:
        return int(chamado_id) if chamado_id is not None else None
    except (TypeError, ValueError):
        return None


def gerar_audio_tts(body):
    body = body or {}
    texto = str(body.get("text") or "").strip()
    voice_key = str(body.get("voice") or DEFAULT_VOICE).strip().casefold()
    chamado_id = body.get("chamadoId") or body.get("chamado_id")

    if not texto:
        raise ValueError("Campo 'text' é obrigatório")

    if len(texto) > MAX_TTS_TEXT_LENGTH:
        raise ValueError(f"Campo 'text' deve ter até {MAX_TTS_TEXT_LENGTH} caracteres")

    if not _texto_tts_permitido(texto):
        raise ValueError("Texto não permitido para TTS")

    voice = VOICES.get(voice_key)
    if not voice:
        raise ValueError("Voz inválida")

    audio_bytes = asyncio.run(_gerar_audio_edge_tts(texto, voice))
    if not audio_bytes:
        raise RuntimeError("Nenhum áudio gerado")

    registrar_auditoria(
        AcaoAuditoria.TTS_SOLICITADO,
        entidade="tts",
        entidade_id=_entidade_id_chamado(chamado_id),
        descricao=(
            "TTS gerado com sucesso. "
            f"voice={voice_key} tamanho_texto={len(texto)}"
        ),
    )

    return audio_bytes


__all__ = [
    "DEFAULT_VOICE",
    "MAX_TTS_TEXT_LENGTH",
    "TERMOS_CLINICOS_BLOQUEADOS",
    "VOICES",
    "_gerar_audio_edge_tts",
    "_texto_tts_permitido",
    "_tts_rate_limit",
    "gerar_audio_tts",
    "registrar_auditoria",
]
