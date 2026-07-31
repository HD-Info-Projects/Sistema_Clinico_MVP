from flask import (
    Blueprint, request, jsonify
)

from flask_jwt_extended import get_jwt_identity, jwt_required
from src.models.auditoria_model import AcaoAuditoria
from src.security.decorators import roles_required
from src.services.auditoria_service import registrar_auditoria

import json

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.db.handler_redis_db import ConnectionDBRedis

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

CACHE_KEY_PACIENTES = "dashboard:pacientes"
CACHE_TTL = 300


@dashboard_bp.route("/pacientes", methods=["GET"])
@jwt_required()
@roles_required("medico")
def dashboard_paciente_lista():
    try:
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
                WHERE a.ID_TBCENCUS = 340
                AND tb.COD = 10460
                AND CAST(a.DATA_HORA_ENTRADA AS DATE) = CURRENT_DATE - 3
                ORDER BY a.DATA_HORA_ENTRADA DESC;
            """)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            
            #redis_connection.set_cache(CACHE_KEY_PACIENTES, json.dumps(result, default=str), ttl=CACHE_TTL)

            registrar_auditoria(
                AcaoAuditoria.VISUALIZOU_PRONTUARIO,
                entidade="dashboard_pacientes",
                usuario_id=int(get_jwt_identity()),
                descricao=f"Listagem de pacientes do dashboard. total={len(result)}",
            )

            return jsonify(result), 200

        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
