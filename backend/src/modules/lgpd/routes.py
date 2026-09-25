from datetime import date

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.modules.lgpd.service import listar_auditorias, listar_retencao_exames, parse_data, registrar_auditoria
from src.security.decorators import roles_required
from src.security.roles import COORD_RECEPCAO_ROLES, LGPD_ROLES
from src.security.unidades import unidade_atual_required
from src.shared.performance_monitoring import iniciar_probe
from src.shared.response_cache import cache_ttl, chave_cache, obter_cache_json, salvar_cache_json
from src.settings.extensions import db

auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/auditorias")
retencao_exames_bp = Blueprint("retencao_exames", __name__, url_prefix="/retencao-exames")


def _bool_param(valor):
    return str(valor or "").strip().lower() in {"1", "true", "sim", "s", "yes", "on"}


@auditoria_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required(*LGPD_ROLES)
def listar_eventos_auditoria():
    return jsonify(listar_auditorias(request.args)), 200


@retencao_exames_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required(*COORD_RECEPCAO_ROLES)
def listar_retencao():
    try:
        hoje = date.today()
        data_ini = parse_data(request.args.get("dataIni"), hoje.replace(day=1))
        data_fim = parse_data(request.args.get("dataFim"), hoje)

        if data_fim < data_ini:
            return jsonify({"error": "dataFim não pode ser menor que dataIni."}), 400

        unidade = unidade_atual_required()
        force_refresh = _bool_param(request.args.get("refresh") or request.args.get("sincronizar"))
        probe = iniciar_probe(
            "retencao_exames",
            unidade_id=unidade.id,
            data_ini=data_ini.isoformat(),
            data_fim=data_fim.isoformat(),
            force_refresh=force_refresh,
        )
        cache_key = chave_cache(
            "retencao_exames:response:v1",
            unidade_id=unidade.id,
            data_ini=data_ini.isoformat(),
            data_fim=data_fim.isoformat(),
        )
        if not force_refresh:
            with probe.etapa("cache_response_get"):
                cached = obter_cache_json(cache_key)
            if cached is not None:
                registrar_auditoria(
                    AcaoAuditoria.VISUALIZOU_RETENCAO_EXAMES,
                    entidade="retencao_exames",
                    usuario_id=int(get_jwt_identity()),
                    descricao=f"Listagem de retenção de exames em cache. data_ini={data_ini} data_fim={data_fim}",
                )
                probe.valor("cache_response_hit", True)
                probe.finalizar(source="response_cache", items_count=len(cached.get("items", [])))
                response = jsonify(cached)
                response.headers["X-Cache"] = "HIT"
                return response, 200

        probe.valor("cache_response_hit", False)
        with probe.etapa("service_listar_retencao_exames"):
            resultado = listar_retencao_exames(
                data_ini,
                data_fim,
                unidade=unidade,
            )
        salvar_cache_json(cache_key, resultado, ttl=cache_ttl())
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_RETENCAO_EXAMES,
            entidade="retencao_exames",
            usuario_id=int(get_jwt_identity()),
            descricao=f"Listagem de retenção de exames. data_ini={data_ini} data_fim={data_fim}",
        )
        probe.finalizar(source="service", items_count=len(resultado.get("items", [])))
        response = jsonify(resultado)
        response.headers["X-Cache"] = "MISS"
        return response, 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar retenção de exames")
        return jsonify({"error": "Erro interno ao listar retenção de exames"}), 500


__all__ = ["auditoria_bp", "listar_eventos_auditoria", "listar_retencao", "retencao_exames_bp"]
