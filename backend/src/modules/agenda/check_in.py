from datetime import date, datetime, time
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, or_, select

from src.models.auditoria_model import AcaoAuditoria
from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.medico_model import Medico
from src.models.model_mydsystem.med_atendimentos_model import MedAtendimentos
from src.models.model_mydsystem.med_spdata_convenios_model import MedSpdataConvenio
from src.security.decorators import roles_required
from src.security.unidades import unidade_atual_required
from src.services.auditoria_service import registrar_auditoria
from src.settings.extensions import db
from src.utils.tuss import (
    TIPOS_PROCEDIMENTO_VALIDOS,
    label_tipo_procedimento,
    normalizar_codigo_tuss,
    tipo_procedimento_codigo,
)


check_in_bp = Blueprint("check_in", __name__, url_prefix="/check_in")

MAX_PAGE_SIZE = 100

STATUS_VALIDOS = {
    "agendado",
    "em-espera",
    "em-atendimento",
    "atendido",
    "faltou",
}

STATUS_LOCAL_ALIASES = {
    "EM_ATENDIMENTO": "em-atendimento",
    "em_atendimento": "em-atendimento",
    "em-atendimento": "em-atendimento",
    "ATENDIDO": "atendido",
    "atendido": "atendido",
    "FALTOU": "faltou",
    "faltou": "faltou",
}

RESUMO_KEYS = {
    "agendado": "agendados",
    "em-espera": "emEspera",
    "em-atendimento": "emAtendimento",
    "atendido": "atendidos",
    "faltou": "faltas",
}


def normalizar_valor(valor):
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    return valor


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def normalizar_int(valor):
    if valor is None:
        return None

    texto = normalizar_texto(valor)
    if not texto:
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        try:
            return int(float(texto.replace(",", ".")))
        except (TypeError, ValueError):
            return None


def calcular_idade(data_nascimento):
    if data_nascimento is None:
        return None
    if isinstance(data_nascimento, str):
        try:
            data_nascimento = datetime.fromisoformat(str(data_nascimento)[:10]).date()
        except ValueError:
            return None
    if not isinstance(data_nascimento, date):
        return None

    hoje = date.today()
    idade = hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )
    return idade if idade >= 0 else None


def normalizar_codigo_procedimento(valor):
    return normalizar_codigo_tuss(valor)


def codigo_procedimento_row(row):
    if normalizar_texto(row.get("COD_PROCEDIMENTO_SPDATA")):
        return normalizar_codigo_procedimento(row.get("COD_PROCEDIMENTO_SPDATA"))

    return normalizar_codigo_procedimento(row.get("PROCEDIMENTO"))


def tipo_procedimento_row(row):
    return tipo_procedimento_codigo(codigo_procedimento_row(row))


def normalizar_identificador_medico(valor):
    valor = normalizar_texto(valor)
    if not valor:
        return ""

    if not valor.replace(".", "").replace(",", "").strip("0"):
        return ""

    return valor


def normalizar_especialidade(valor):
    texto = normalizar_texto(valor)
    if not texto or texto == "0" or texto.casefold() == "não informado":
        return ""
    return texto


def normalizar_status_local(status):
    return STATUS_LOCAL_ALIASES.get(normalizar_texto(status))


def status_repacagd(valor):
    atendido = normalizar_texto(valor).upper()
    if atendido == "S":
        return "em-espera"
    if atendido == "N":
        return "agendado"
    return "desconhecido"


def status_para_resumo():
    return {
        "agendados": 0,
        "emEspera": 0,
        "emAtendimento": 0,
        "atendidos": 0,
        "faltas": 0,
        "desconhecidos": 0,
    }


def parse_int_param(nome, default, minimo=1, maximo=None):
    valor = request.args.get(nome, default=default, type=int)
    valor = max(valor or default, minimo)
    if maximo is not None:
        valor = min(valor, maximo)
    return valor


def parse_data_param():
    valor = request.args.get("data")
    if not valor:
        return date.today()
    return datetime.fromisoformat(str(valor)[:10]).date()


def row_para_dict(row, nomes_colunas):
    return {
        nome: normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def buscar_agendamentos_firebird(data_ref, unidade, medico=None, q=None):
    where = ["CAST(r.DATA AS DATE) = ?"]
    params = [data_ref]

    codigo_agenda = normalizar_texto(getattr(unidade, "codigo_spdata_agenda", None))
    if not codigo_agenda:
        raise ValueError("Unidade sem código SPDATA de agenda configurado")

    where.append("CAST(r.UNIDADE AS VARCHAR(50)) = ?")
    params.append(codigo_agenda)

    medico = normalizar_texto(medico)
    if medico:
        where.append(
            "("
            "CAST(r.CRM_ATEND AS VARCHAR(50)) = ? "
            "OR CAST(r.CRM AS VARCHAR(50)) = ? "
            "OR r.NOME = ?"
            ")"
        )
        params.extend([medico, medico, medico])

    q = normalizar_texto(q)
    if q:
        where.append(
            "(r.PACIENTE CONTAINING ? "
            "OR r.CPF CONTAINING ? "
            "OR r.PRONT CONTAINING ? "
            "OR CAST(r.REGISTRO AS VARCHAR(50)) CONTAINING ?)"
        )
        params.extend([q, q, q, q])

    sql = f"""
        SELECT
            r.ID AS ID_AGENDAMENTO,
            r.REGISTRO AS REGISTRO,
            r.GRV_ATE AS GRV_ATE,
            r.NOME AS MEDICO,
            r.CRM AS CRM,
            r.CRM_ATEND AS CRM_ATEND,
            r.DATA AS DATA,
            r.HORA AS HORA,
            r.HR_AGE AS HR_AGE,
            r.PACIENTE AS PACIENTE,
            r.CPF AS CPF,
            r.PRONT AS PRONTUARIO,
            r.CONV AS ID_CONVENIO_SPDATA,
            r.CONV AS CONVENIO,
            r.FONE AS FONE,
            r.CELULAR AS CELULAR,
            r.EMAIL AS EMAIL,
            CASE
                WHEN r.ESPEC IS NOT NULL AND r.ESPEC <> 0 THEN esp_agenda.NOME
                WHEN prof.ESP_PRINC IS NOT NULL AND prof.ESP_PRINC <> 0 THEN esp_princ.NOME
                ELSE NULL
            END AS ESPECIALIDADE,
            r.UNIDADE AS UNIDADE,
            r.RETORNO AS RETORNO,
            r.TP_AGE AS TIPO_AGENDA,
            r.PROC_SOL AS PROCEDIMENTO_SOLICITADO,
            r.PROCED AS COD_PROCEDIMENTO_SPDATA,
            r.PROCED AS PROCEDIMENTO,
            r.OBS AS OBS,
            r.DATA_NASCIMENTO AS DATA_NASCIMENTO,
            r.ATENDIDO AS ATENDIDO,
            r.ID_RICADPAC AS ID_PACIENTE_SPDATA,
            r.DATA_HORA_AGENDAMENTO AS DATA_HORA_AGENDAMENTO
        FROM REPACAGD r
        LEFT JOIN TBESPEC esp_agenda
            ON esp_agenda.COD = r.ESPEC
        LEFT JOIN TBPROFIS prof
            ON prof.ID = (
                SELECT FIRST 1 cb.ID_TBPROFIS
                FROM TBCBOPRO cb
                WHERE CAST(cb.COD AS VARCHAR(50)) = CAST(r.CRM AS VARCHAR(50))
                ORDER BY cb.ATIVO DESC, cb.ID
            )
        LEFT JOIN TBESPEC esp_princ
            ON esp_princ.COD = prof.ESP_PRINC
        WHERE {' AND '.join(where)}
        ORDER BY r.DATA, r.HORA, r.PACIENTE
    """

    with ConnectionDBFireBird() as con:
        cursor = con.cursor()
        cursor.execute(sql, tuple(params))
        nomes_colunas = [desc[0].strip().upper() for desc in cursor.description]
        return [row_para_dict(row, nomes_colunas) for row in cursor.fetchall()]


def buscar_atendimentos_firebird(data_ref, unidade):
    sql = """
        SELECT
            a.ID AS ID_ATENDIMENTO,
            a.COD_ATENDIMENTO AS REGISTRO,
            a.COD_ATENDIMENTO AS COD_ATENDIMENTO,
            a.ID_RICADPAC AS ID_PACIENTE_SPDATA,
            CAST(a.DATA_HORA_ENTRADA AS DATE) AS DATA,
            CAST(a.DATA_HORA_ENTRADA AS TIME) AS HORA,
            a.DATA_HORA_ENTRADA AS DATA_HORA_AGENDAMENTO,
            a.DATA_HORA_ALTA_MEDICA AS DATA_HORA_ALTA_MEDICA,
            a.OBS_ATENDIMENTO AS OBS,
            a.ID_TBCONVEN AS ID_CONVENIO_SPDATA,
            COALESCE(convenio.NOME, CAST(a.ID_TBCONVEN AS VARCHAR(50))) AS CONVENIO,
            a.ID_TBCENCUS AS UNIDADE,

            paciente.PRONT AS PRONTUARIO,
            paciente.NOME AS PACIENTE,
            paciente.NASC AS DATA_NASCIMENTO,
            paciente.CELULAR AS CELULAR,
            paciente.EMAIL AS EMAIL,
            paciente.CPF AS CPF,
            paciente.ENDERECO AS ENDERECO,

            medico.NOME AS MEDICO,
            tb.COD AS CRM,
            tb.COD AS CRM_ATEND,

            CAST(NULL AS INTEGER) AS ID_AGENDAMENTO,
            CAST(NULL AS INTEGER) AS GRV_ATE,
            CAST(NULL AS VARCHAR(30)) AS FONE,
            COALESCE(esp_atendimento.NOME, esp_princ.NOME) AS ESPECIALIDADE,
            CAST(NULL AS VARCHAR(50)) AS RETORNO,
            CAST(NULL AS VARCHAR(50)) AS TIPO_AGENDA,
            CAST(NULL AS VARCHAR(255)) AS PROCEDIMENTO_SOLICITADO,
            procedimento.COD_PROCEDIMENTO AS COD_PROCEDIMENTO_SPDATA,
            procedimento.NOME AS PROCEDIMENTO,
            'S' AS ATENDIDO,
            'S' AS TEM_ATENDIMENTO
        FROM ATCABECATEND a
        INNER JOIN RICADPAC paciente
            ON paciente.ID = a.ID_RICADPAC
        INNER JOIN TBCBOPRO tb
            ON a.ID_TBCBOPRO_ATENDIMENTO = tb.ID
        INNER JOIN TBPROFIS medico
            ON tb.ID_TBPROFIS = medico.ID
        LEFT JOIN TBCONVEN convenio
            ON convenio.COD = a.ID_TBCONVEN
        LEFT JOIN TBPROCTO procedimento
            ON procedimento.ID = a.ID_TBPROCTO
        LEFT JOIN TBESPEC esp_atendimento
            ON esp_atendimento.COD = (
                SELECT FIRST 1 me.ESP
                FROM TBMEDESP me
                WHERE me.ID_TBCBOPRO = tb.ID
                  AND me.ATIVO = 'T'
                  AND me.ESP <> 0
                ORDER BY me.ESP
            )
        LEFT JOIN TBESPEC esp_princ
            ON esp_princ.COD = medico.ESP_PRINC
        WHERE a.ID_TBCENCUS = ?
          AND CAST(a.DATA_HORA_ENTRADA AS DATE) = ?
        ORDER BY a.DATA_HORA_ENTRADA, paciente.NOME
    """

    with ConnectionDBFireBird() as con:
        cursor = con.cursor()
        cursor.execute(sql, (unidade.codigo_spdata_centro_custo, data_ref))
        nomes_colunas = [desc[0].strip().upper() for desc in cursor.description]
        return [row_para_dict(row, nomes_colunas) for row in cursor.fetchall()]


def chave_registro(row):
    return normalizar_texto(row.get("REGISTRO") or row.get("COD_ATENDIMENTO"))


def preencher_vazios(base, extra):
    merged = dict(base)
    for key, value in extra.items():
        if value is None:
            continue
        if normalizar_texto(merged.get(key)):
            continue
        merged[key] = value
    return merged


def mesclar_agenda_atendimentos(rows_agenda, rows_atendimentos):
    por_registro = {}
    sem_registro = []

    for row in rows_agenda:
        key = chave_registro(row)
        if key:
            por_registro[key] = row
        else:
            sem_registro.append(row)

    for row in rows_atendimentos:
        key = chave_registro(row)
        row["TEM_ATENDIMENTO"] = "S"
        if not key:
            sem_registro.append(row)
            continue

        if key in por_registro:
            merged = preencher_vazios(por_registro[key], row)
            merged["TEM_ATENDIMENTO"] = "S"
            merged["ID_ATENDIMENTO"] = row.get("ID_ATENDIMENTO")
            merged["DATA_HORA_ALTA_MEDICA"] = row.get("DATA_HORA_ALTA_MEDICA")
            por_registro[key] = merged
        else:
            por_registro[key] = row

    return [*por_registro.values(), *sem_registro]


def filtrar_rows(rows, medico=None, q=None):
    medico = normalizar_texto(medico)
    q = normalizar_texto(q).casefold()
    filtrados = []

    for row in rows:
        if medico:
            medicos_possiveis = {
                normalizar_identificador_medico(row.get("CRM_ATEND")),
                normalizar_identificador_medico(row.get("CRM")),
                normalizar_texto(row.get("MEDICO")),
            }
            medicos_possiveis.discard("")
            if medico not in medicos_possiveis:
                continue

        if q:
            campos_busca = [
                row.get("PACIENTE"),
                row.get("CPF"),
                row.get("PRONTUARIO"),
                row.get("REGISTRO"),
                row.get("COD_ATENDIMENTO"),
            ]
            texto = " ".join(normalizar_texto(campo).casefold() for campo in campos_busca)
            if q not in texto:
                continue

        filtrados.append(row)

    return filtrados


def filtrar_rows_por_tipo(rows, tipo=None):
    tipo = normalizar_texto(tipo)
    if not tipo:
        return rows

    return [row for row in rows if tipo_procedimento_row(row) == tipo]


def buscar_status_local(registros, unidade=None):
    registros = [normalizar_texto(registro) for registro in registros if normalizar_texto(registro)]
    if not registros:
        return {}

    filtros = [MedAtendimentos.cod_atendimento.in_(registros)]
    if unidade:
        filtros.append(or_(
            MedAtendimentos.unidade_id == unidade.id,
            MedAtendimentos.unidade_id.is_(None),
        ))

    rows = db.session.execute(select(MedAtendimentos).where(and_(*filtros))).scalars().all()

    status_por_registro = {}
    for row in rows:
        cod_atendimento = normalizar_texto(row.cod_atendimento)
        status = normalizar_status_local(row.status)
        if cod_atendimento and status and cod_atendimento not in status_por_registro:
            status_por_registro[cod_atendimento] = {
                "status": status,
                "medsystemAtendimentoId": row.id,
            }

    return status_por_registro


def buscar_convenios_locais(codigos_spdata):
    codigos = sorted({
        codigo
        for codigo in (normalizar_int(codigo) for codigo in codigos_spdata)
        if codigo is not None
    })
    if not codigos:
        return {}

    rows = db.session.execute(
        select(MedSpdataConvenio.codigo_spdata, MedSpdataConvenio.nome).where(
            MedSpdataConvenio.codigo_spdata.in_(codigos)
        )
    ).all()

    return {
        codigo: nome
        for codigo, nome in rows
        if normalizar_texto(nome)
    }


def buscar_especialidades_medicos_locais(rows):
    chaves = sorted({
        chave
        for row in rows
        for chave in (
            normalizar_identificador_medico(row.get("CRM_ATEND")),
            normalizar_identificador_medico(row.get("CRM")),
        )
        if chave
    })
    if not chaves:
        return {}

    registros = db.session.execute(
        select(Medico).where(
            Medico.ativo.is_(True),
            or_(
                Medico.crm_atendimento_spdata.in_(chaves),
                Medico.crm.in_(chaves),
            ),
        )
    ).scalars().all()

    especialidades = {}
    for registro in registros:
        especialidade = normalizar_especialidade(registro.especialidade)
        if not especialidade:
            continue

        for valor in (registro.crm_atendimento_spdata, registro.crm):
            chave = normalizar_identificador_medico(valor)
            if chave and chave not in especialidades:
                especialidades[chave] = especialidade

    return especialidades


def convenio_para_frontend(row, convenios_por_codigo):
    codigo = normalizar_int(row.get("ID_CONVENIO_SPDATA") or row.get("CONVENIO"))
    if codigo is None:
        return ""

    return convenios_por_codigo.get(codigo, "")


def especialidade_para_frontend(row, especialidades_por_medico):
    for chave in (
        normalizar_identificador_medico(row.get("CRM_ATEND")),
        normalizar_identificador_medico(row.get("CRM")),
    ):
        especialidade = especialidades_por_medico.get(chave)
        if especialidade:
            return especialidade

    return normalizar_especialidade(row.get("ESPECIALIDADE"))


def item_para_frontend(row, status_local, convenios_por_codigo, especialidades_por_medico, unidade):
    registro = normalizar_texto(row.get("REGISTRO"))
    id_convenio_spdata = normalizar_int(row.get("ID_CONVENIO_SPDATA") or row.get("CONVENIO"))
    codigo_procedimento = codigo_procedimento_row(row) or None
    tipo_procedimento = tipo_procedimento_row(row)
    local = status_local.get(registro)
    if local:
        status = local["status"]
    elif normalizar_texto(row.get("TEM_ATENDIMENTO")).upper() == "S":
        status = "em-espera"
    else:
        status = status_repacagd(row.get("ATENDIDO"))
    crm_atendimento = normalizar_texto(row.get("CRM_ATEND"))
    crm = normalizar_texto(row.get("CRM"))
    crm_atendimento_key = normalizar_identificador_medico(row.get("CRM_ATEND"))
    crm_key = normalizar_identificador_medico(row.get("CRM"))

    return {
        "id": row.get("ID_AGENDAMENTO") or registro,
        "clinicaId": unidade.id,
        "unidadeId": unidade.id,
        "registro": registro,
        "grvAte": row.get("GRV_ATE"),
        "medsystemAtendimentoId": local["medsystemAtendimentoId"] if local else None,
        "idPacienteSpdata": row.get("ID_PACIENTE_SPDATA"),
        "data": row.get("DATA"),
        "horario": row.get("HORA") or row.get("HR_AGE") or "",
        "paciente": normalizar_texto(row.get("PACIENTE")),
        "cpf": normalizar_texto(row.get("CPF")),
        "prontuario": normalizar_texto(row.get("PRONTUARIO")),
        "convenio": convenio_para_frontend(row, convenios_por_codigo),
        "idConvenioSpdata": id_convenio_spdata,
        "telefone": normalizar_texto(row.get("FONE")),
        "celular": normalizar_texto(row.get("CELULAR")),
        "email": normalizar_texto(row.get("EMAIL")),
        "medico": normalizar_texto(row.get("MEDICO")),
        "crm": crm,
        "crmAtendimento": crm_atendimento,
        "medicoKey": crm_atendimento_key or crm_key or normalizar_texto(row.get("MEDICO")),
        "especialidade": especialidade_para_frontend(row, especialidades_por_medico),
        "unidade": normalizar_texto(row.get("UNIDADE")),
        "retorno": normalizar_texto(row.get("RETORNO")),
        "tipoAgenda": normalizar_texto(row.get("TIPO_AGENDA")),
        "codigoProcedimentoSpdata": codigo_procedimento,
        "tipoProcedimento": tipo_procedimento,
        "tipoProcedimentoLabel": label_tipo_procedimento(tipo_procedimento),
        "procedimentoSolicitado": normalizar_texto(row.get("PROCEDIMENTO_SOLICITADO")),
        "procedimento": normalizar_texto(row.get("PROCEDIMENTO")),
        "observacao": normalizar_texto(row.get("OBS")),
        "dataNascimento": row.get("DATA_NASCIMENTO"),
        "idade": calcular_idade(row.get("DATA_NASCIMENTO")),
        "dataHoraAgendamento": row.get("DATA_HORA_AGENDAMENTO"),
        "atendidoSpdata": normalizar_texto(row.get("ATENDIDO")),
        "status": status,
        "statusOrigem": "medsystem" if local else "spdata",
    }


def calcular_resumo(items):
    resumo = status_para_resumo()
    for item in items:
        key = RESUMO_KEYS.get(item["status"], "desconhecidos")
        resumo[key] += 1
    return resumo


def calcular_medicos(rows, especialidades_por_medico):
    medicos = {}
    for row in rows:
        nome = normalizar_texto(row.get("MEDICO"))
        crm_atendimento = normalizar_texto(row.get("CRM_ATEND"))
        crm = normalizar_texto(row.get("CRM"))
        especialidade = especialidade_para_frontend(row, especialidades_por_medico)
        key = (
            normalizar_identificador_medico(row.get("CRM_ATEND"))
            or normalizar_identificador_medico(row.get("CRM"))
            or nome
        )
        if not key:
            continue

        if key not in medicos:
            medicos[key] = {
                "id": key,
                "nome": nome or "Médico não informado",
                "crm": crm,
                "crmAtendimento": crm_atendimento,
                "especialidade": especialidade,
                "pacientesCount": 0,
            }
        elif not medicos[key]["especialidade"] and especialidade:
            medicos[key]["especialidade"] = especialidade
        medicos[key]["pacientesCount"] += 1

    return sorted(medicos.values(), key=lambda item: item["nome"])


@check_in_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("recepcao", "admin")
def home_check_in():
    try:
        data_ref = parse_data_param()
        unidade = unidade_atual_required()
        page = parse_int_param("page", 1)
        page_size = parse_int_param("pageSize", 20, maximo=MAX_PAGE_SIZE)
        status_filtro = normalizar_texto(request.args.get("status"))
        tipo_filtro = normalizar_texto(request.args.get("tipo"))
        medico = request.args.get("medico")
        q = request.args.get("q")

        if status_filtro and status_filtro not in STATUS_VALIDOS:
            return jsonify({"error": "Status inválido"}), 400
        if tipo_filtro and tipo_filtro not in TIPOS_PROCEDIMENTO_VALIDOS:
            return jsonify({"error": "Tipo inválido"}), 400

        rows_agenda = buscar_agendamentos_firebird(data_ref, unidade)
        rows_atendimentos = buscar_atendimentos_firebird(data_ref, unidade)
        rows_dia = mesclar_agenda_atendimentos(rows_agenda, rows_atendimentos)
        rows_tipo = filtrar_rows_por_tipo(rows_dia, tipo_filtro)
        rows_filtradas = filtrar_rows(rows_tipo, medico=medico, q=q)

        registros = [row.get("REGISTRO") for row in rows_filtradas]
        status_local = buscar_status_local(registros, unidade)
        convenios_por_codigo = buscar_convenios_locais(
            row.get("ID_CONVENIO_SPDATA") or row.get("CONVENIO")
            for row in rows_filtradas
        )
        especialidades_por_medico = buscar_especialidades_medicos_locais(rows_dia)
        items_com_status = [
            item_para_frontend(row, status_local, convenios_por_codigo, especialidades_por_medico, unidade)
            for row in rows_filtradas
        ]

        resumo = calcular_resumo(items_com_status)

        if status_filtro:
            items_filtrados = [item for item in items_com_status if item["status"] == status_filtro]
        else:
            items_filtrados = items_com_status

        total = len(items_filtrados)
        start = (page - 1) * page_size
        end = start + page_size

        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_CHECK_IN,
            entidade="check_in",
            usuario_id=int(get_jwt_identity()),
            descricao=f"Listagem de check-in. data={data_ref} page={page} page_size={page_size} total={total}",
        )

        return jsonify({
            "items": items_filtrados[start:end],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "medicos": calcular_medicos(rows_tipo, especialidades_por_medico),
            "resumo": resumo,
            "data": data_ref.isoformat(),
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao listar check-in")
        return jsonify({"error": "Erro interno ao listar check-in"}), 500
