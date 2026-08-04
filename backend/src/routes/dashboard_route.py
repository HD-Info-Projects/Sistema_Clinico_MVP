from datetime import date

from flask import Blueprint, current_app, jsonify

from flask_jwt_extended import get_jwt_identity, jwt_required
from src.models.auditoria_model import AcaoAuditoria
from src.security.decorators import roles_required
from src.services.auditoria_service import registrar_auditoria
from src.services.spdata_atendimentos_service import get_crm_medico_usuario, listar_agenda_medica

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

def _data_hora_entrada(item):
    data = item.get("data") or date.today().isoformat()
    horario = item.get("horario") or "00:00"
    return f"{data}T{horario}:00"


def _item_dashboard(item, crm_medico):
    paciente = item.get("paciente") or {}
    return {
        "ID_ATENDIMENTO": item.get("spdataAtendimentoId") or item.get("id"),
        "COD_ATENDIMENTO": item.get("codAtendimento") or item.get("id"),
        "ID_PACIENTE": item.get("pacienteId"),
        "TP_ATENDIMENTO": None,
        "DATA_HORA_ENTRADA": _data_hora_entrada(item),
        "DATA_HORA_ALTA_MEDICA": None,
        "OBS_ATENDIMENTO": item.get("descricao") or "",
        "ID_TBCONVEN": paciente.get("idConvenioSpdata"),
        "PRONTUARIO": "",
        "PACIENTE": paciente.get("nome") or "Paciente",
        "DATA_NASCIMENTO": paciente.get("dataNascimento") or "",
        "SEXO": paciente.get("sexo") or "",
        "CELULAR": "",
        "EMAIL": "",
        "CPF": "",
        "ENDERECO": "",
        "ID_MEDICO": item.get("medicoId"),
        "MEDICO": "",
        "CRM_MEDICO": crm_medico,
    }


@dashboard_bp.route("/pacientes", methods=["GET"])
@jwt_required()
@roles_required("medico")
def dashboard_paciente_lista():
    try:
        usuario_id = int(get_jwt_identity())
        hoje = date.today()
        crm_medico = get_crm_medico_usuario(usuario_id)
        items = listar_agenda_medica(usuario_id, hoje, hoje)
        result = [_item_dashboard(item, crm_medico) for item in items]

        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_AGENDA,
            entidade="dashboard_pacientes",
            usuario_id=usuario_id,
            descricao=f"Listagem de pacientes do dashboard. total={len(result)}",
        )

        return jsonify(result), 200

    except Exception:
        current_app.logger.exception("Erro ao listar pacientes do dashboard")
        return jsonify({"error": "Erro interno ao listar pacientes do dashboard"}), 500
