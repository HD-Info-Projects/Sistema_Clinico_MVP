from flask import Blueprint, Response, current_app, jsonify, request

from src.modules.chamadas import service
from src.settings.extensions import limiter


tts_bp = Blueprint("tts", __name__, url_prefix="/tts")


@tts_bp.route("/speak", methods=["POST"])
@limiter.limit(service._tts_rate_limit)
def speak():
    if not current_app.config.get("ENABLE_TTS", False):
        return jsonify({"error": "TTS desabilitado"}), 503

    try:
        audio_bytes = service.gerar_audio_tts(request.get_json(silent=True) or {})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except ModuleNotFoundError as e:
        if e.name != "edge_tts":
            raise

        current_app.logger.exception("Dependência edge-tts indisponível")
        return jsonify({"error": "Dependência edge-tts não instalada"}), 500
    except RuntimeError as e:
        if str(e) == "Nenhum áudio gerado":
            return jsonify({"error": str(e)}), 500

        current_app.logger.exception("Falha ao gerar TTS")
        return jsonify({"error": "Erro ao gerar TTS"}), 500
    except Exception:
        current_app.logger.exception("Falha ao gerar TTS")
        return jsonify({"error": "Erro ao gerar TTS"}), 500

    return Response(
        audio_bytes,
        mimetype="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-store",
        },
    )


__all__ = ["speak", "tts_bp"]
