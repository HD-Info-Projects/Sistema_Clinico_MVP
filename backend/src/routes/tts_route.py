"""Compatibility wrapper for chamadas/TTS routes."""

from src.modules.chamadas.routes import speak, tts_bp
from src.modules.chamadas.service import (
    DEFAULT_VOICE,
    MAX_TTS_TEXT_LENGTH,
    TERMOS_CLINICOS_BLOQUEADOS,
    VOICES,
    _gerar_audio_edge_tts,
    _texto_tts_permitido,
    _tts_rate_limit,
    registrar_auditoria,
)

__all__ = [
    "DEFAULT_VOICE",
    "MAX_TTS_TEXT_LENGTH",
    "TERMOS_CLINICOS_BLOQUEADOS",
    "VOICES",
    "_gerar_audio_edge_tts",
    "_texto_tts_permitido",
    "_tts_rate_limit",
    "registrar_auditoria",
    "speak",
    "tts_bp",
]
