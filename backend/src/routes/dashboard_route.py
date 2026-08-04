from datetime import date, datetime

from flask import Blueprint, request, jsonify

from flask_jwt_extended import get_jwt_identity, jwt_required
from src.security.decorators import roles_required
from src.security.unidades import unidade_atual_required
from src.services.spdata_atendimentos_service import get_crm_medico_usuario

from src.models.db.handler_fb_db import ConnectionDBFireBird

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def parse_data(valor):
    if not valor:
        return date.today()
    return datetime.fromisoformat(str(valor)[:10]).date()


@dashboard_bp.route("/pacientes", methods=["GET"])
@jwt_required()
@roles_required("medico")
def dashboard_paciente_lista():
    try:
        usuario_id = int(get_jwt_identity())
        unidade = unidade_atual_required()
        crm_medico = get_crm_medico_usuario(usuario_id)
        data_ref = parse_data(request.args.get("data"))

        # redis_connection = ConnectionDBRedis()
        # cached = redis_connection.get_cache(CACHE_KEY_PACIENTES)
        # if cached is not None:
        #     return jsonify(json.loads(cached)), 200
        
        with ConnectionDBFireBird() as con:
            cursor = con.cursor()
            # cursor.execute("""
            # SELECT *
            # FROM ATCABECATEND a
            # WHERE a.id_tbcencus = '350'
            # AND CAST(a.DATA_HORA_ENTRADA AS DATE) = CURRENT_DATE;
            # """)
            
            # Query de SELECT:
            cursor.execute("""
                SELECT
                a.ID AS ID_ATENDIMENTO,
                    a.COD_ATENDIMENTO,
                    a.ID_RICADPAC AS ID_PACIENTE,
                    a.TP_ATENDIMENTO,
                    a.DATA_HORA_ENTRADA,
                    a.DATA_HORA_ALTA_MEDICA,
                    a.OBS_ATENDIMENTO,
                    a.ID_TBCONVEN AS ID_TBCONVEN,

                    paciente.PRONT AS PRONTUARIO,
                    paciente.NOME AS PACIENTE,
                    paciente.NASC AS DATA_NASCIMENTO,
                    paciente.SEXO AS SEXO,
                    paciente.CELULAR AS CELULAR,
                    paciente.EMAIL AS EMAIL,
                    paciente.CPF AS CPF,
                    paciente.ENDERECO AS ENDERECO,

                    medico.ID AS ID_MEDICO,
                    medico.NOME AS MEDICO,
                    tb.cod AS CRM_MEDICO
                FROM ATCABECATEND a
                INNER JOIN RICADPAC paciente
                    ON paciente.ID = a.ID_RICADPAC
                INNER JOIN TBCBOPRO tb
                    ON a.ID_TBCBOPRO_ATENDIMENTO = tb.ID
                INNER JOIN TBPROFIS medico
                    ON tb.ID_TBPROFIS = medico.ID
                WHERE a.ID_TBCENCUS = ?
                AND tb.COD = ?
                AND CAST(a.DATA_HORA_ENTRADA AS DATE) = ?
                ORDER BY a.DATA_HORA_ENTRADA DESC;
            """, (unidade.codigo_spdata_centro_custo, crm_medico, data_ref))

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            
            #redis_connection.set_cache(CACHE_KEY_PACIENTES, json.dumps(result, default=str), ttl=CACHE_TTL)

            return jsonify(result), 200

        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
