from datetime import date

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.models.auditoria_model import AcaoAuditoria
from src.modules.lgpd.service import listar_auditorias, listar_retencao_exames, parse_data, registrar_auditoria
from src.security.decorators import roles_required
from src.security.unidades import unidade_atual_required
from src.settings.extensions import db

auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/auditorias")
retencao_exames_bp = Blueprint("retencao_exames", __name__, url_prefix="/retencao-exames")


@auditoria_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("admin", "dpo", "ti")
def listar_eventos_auditoria():
    return jsonify(listar_auditorias(request.args)), 200


@retencao_exames_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("recepcao", "admin")
def listar_retencao():
    try:
        hoje = date.today()
        data_ini = parse_data(request.args.get("dataIni"), hoje.replace(day=1))
        data_fim = parse_data(request.args.get("dataFim"), hoje)

        if data_fim < data_ini:
            return jsonify({"error": "dataFim não pode ser menor que dataIni."}), 400

        resultado = listar_retencao_exames(
            data_ini,
            data_fim,
            unidade=unidade_atual_required(),
        )
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_RETENCAO_EXAMES,
            entidade="retencao_exames",
            usuario_id=int(get_jwt_identity()),
            descricao=f"Listagem de retenção de exames. data_ini={data_ini} data_fim={data_fim}",
        )
        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar retenção de exames")
        return jsonify({"error": "Erro interno ao listar retenção de exames"}), 500


__all__ = ["auditoria_bp", "listar_eventos_auditoria", "listar_retencao", "retencao_exames_bp"]
