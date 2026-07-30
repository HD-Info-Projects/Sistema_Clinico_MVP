from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import and_, or_, select

from src.models.anamnese_model import Anamnese
from src.models.atendimentos_model import Atendimento
from src.models.diagnostico_model import Diagnostico
from src.models.evolucoes_medicas_model import EvolucaoMedica
from src.models.medico_model import Medico
from src.models.model_mydsystem.med_exames_model import Exame
from src.models.model_mydsystem.med_atendimentos_model import (
    MedAtendimentos,
    StatusAtendimentoMedSystem,
)
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.models.model_mydsystem.med_spdata_atendimentos_model import (
    MedSpdataAtendimento,
)
from src.models.model_mydsystem.med_spdata_convenios_model import MedSpdataConvenio
from src.models.prescricao_model import Prescricao
from src.models.solicitacao_exame_model import SolicitacaoExame
from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.services.spdata_agenda_service import sincronizar_agenda_spdata
from src.settings.extensions import db
from src.utils.normalizar import normalizar_cpf


# 340 - Natus
# 350 - Centro AMI

UNIDADE_PADRAO_SPDATA = 340

STATUS_VALIDOS = {
    "em-atendimento",
    "atendido",
    "faltou",
}

STATUS_ALIASES = {
    "EM_ATENDIMENTO": "em-atendimento",
    "em_atendimento": "em-atendimento",
    "em-atendimento": "em-atendimento",
    "ATENDIDO": "atendido",
    "atendido": "atendido",
    "FALTOU": "faltou",
    "faltou": "faltou",
}

STATUS_MEDSYSTEM_VALUES = {
    "em-atendimento": {StatusAtendimentoMedSystem.EM_ATENDIMENTO.value, "em-atendimento"},
    "atendido": {StatusAtendimentoMedSystem.ATENDIDO.value, "atendido"},
    "faltou": {StatusAtendimentoMedSystem.FALTOU.value, "faltou"},
}


def normalizar_valor(valor):
    if valor is None:
        return None

    if isinstance(valor, Decimal):
        return float(valor)

    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()

    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.hex()

    if hasattr(valor, "read"):
        conteudo = valor.read()
        if isinstance(conteudo, bytes):
            try:
                return conteudo.decode("utf-8")
            except UnicodeDecodeError:
                return conteudo.hex()
        return str(conteudo)

    return valor


def normalizar_texto(valor, limite=None):
    if valor is None:
        return None

    valor = str(valor).strip()
    if limite:
        valor = valor[:limite]

    return valor or None


def normalizar_int(valor):
    if valor is None or valor == "":
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def normalizar_data(valor):
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    return datetime.fromisoformat(str(valor)[:10]).date()


def normalizar_datetime(valor):
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor

    if isinstance(valor, date):
        return datetime.combine(valor, time.min)

    texto = str(valor).replace("Z", "")
    return datetime.fromisoformat(texto)


def normalizar_time(valor):
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.time().replace(microsecond=0)

    if isinstance(valor, time):
        return valor.replace(microsecond=0)

    texto = str(valor).strip()
    if len(texto) == 5:
        texto = f"{texto}:00"

    return time.fromisoformat(texto)


def normalizar_status(status):
    if status is None:
        return None

    return STATUS_ALIASES.get(str(status), str(status))


def valores_status_medsystem(status):
    status = normalizar_status(status)
    if status is None:
        return []
    if status not in STATUS_VALIDOS:
        raise ValueError("Status inválido")
    return list(STATUS_MEDSYSTEM_VALUES[status])


def filtrar_agenda_frontend(items, status=None, search=None):
    status = normalizar_status(status)
    if status and status not in STATUS_VALIDOS:
        raise ValueError("Status inválido")

    termo = normalizar_texto(search, 255)
    termo_casefold = termo.casefold() if termo else None

    filtrados = items
    if status:
        filtrados = [item for item in filtrados if item.get("status") == status]
    if termo_casefold:
        filtrados = [
            item for item in filtrados
            if termo_casefold in str(item.get("paciente", {}).get("nome") or "").casefold()
        ]

    return filtrados


def row_para_dict(row, nomes_colunas):
    return {
        nome: normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def get_crm_medico_usuario(usuario_id):
    medico = db.session.execute(
        select(Medico).where(
            Medico.usuario_id == usuario_id,
            Medico.ativo.is_(True),
        )
    ).scalars().first()

    crm_atendimento = normalizar_texto(
        getattr(medico, "crm_atendimento_spdata", None) if medico else None,
        50,
    )
    crm = normalizar_texto(medico.crm, 50) if medico else None

    if not medico or not (crm_atendimento or crm):
        raise ValueError("Médico local não possui crm_atendimento_spdata nem crm configurado para filtrar o SPDATA.")

    return crm_atendimento or crm


def buscar_atendimentos_spdata(data_ini, data_fim, crm_medico):
    sql = """
        SELECT
            a.ID AS SPDATA_ATENDIMENTO_ID,
            a.COD_ATENDIMENTO,
            a.ID_RICADPAC AS ID_PACIENTE_SPDATA,
            a.DATA_HORA_ENTRADA,
            a.DATA_HORA_ALTA_MEDICA,
            a.OBS_ATENDIMENTO,
            a.ID_TBCONVEN AS ID_CONVENIO_SPDATA,
            convenio.NOME AS CONVENIO_NOME,
            a.ID_TBCENCUS AS ID_CENTRO_CUSTO_SPDATA,

            paciente.PRONT AS PRONTUARIO,
            paciente.NOME AS PACIENTE,
            paciente.NASC AS DATA_NASCIMENTO,
            paciente.SEXO AS SEXO,
            paciente.CELULAR AS CELULAR,
            paciente.EMAIL AS EMAIL,
            paciente.CPF AS CPF,
            paciente.ENDERECO AS ENDERECO,

            medico.ID AS ID_MEDICO_SPDATA,
            medico.NOME AS MEDICO,
            tb.COD AS CRM_MEDICO
        FROM ATCABECATEND a
        INNER JOIN RICADPAC paciente
            ON paciente.ID = a.ID_RICADPAC
        INNER JOIN TBCBOPRO tb
            ON a.ID_TBCBOPRO_ATENDIMENTO = tb.ID
        INNER JOIN TBPROFIS medico
            ON tb.ID_TBPROFIS = medico.ID
        LEFT JOIN TBCONVEN convenio
            ON convenio.COD = a.ID_TBCONVEN
        WHERE a.ID_TBCENCUS = ?
          AND tb.COD = ?
          AND CAST(a.DATA_HORA_ENTRADA AS DATE) BETWEEN ? AND ?
        ORDER BY a.DATA_HORA_ENTRADA, paciente.NOME;
    """

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        cursor.execute(
            sql,
            (
                UNIDADE_PADRAO_SPDATA,
                crm_medico,
                data_ini,
                data_fim,
            ),
        )
        nomes_colunas = [descricao[0].strip().upper() for descricao in cursor.description]
        return [row_para_dict(row, nomes_colunas) for row in cursor.fetchall()]


def sincronizar_atendimentos_spdata(data_ini, data_fim, crm_medico):
    dados_spdata = buscar_atendimentos_spdata(data_ini, data_fim, crm_medico)
    ids_spdata = [
        normalizar_int(item.get("SPDATA_ATENDIMENTO_ID"))
        for item in dados_spdata
        if item.get("SPDATA_ATENDIMENTO_ID") is not None
    ]

    existentes = {}
    if ids_spdata:
        registros = db.session.execute(
            select(MedSpdataAtendimento).where(
                MedSpdataAtendimento.spdata_atendimento_id.in_(ids_spdata)
            )
        ).scalars().all()
        existentes = {registro.spdata_atendimento_id: registro for registro in registros}

    total_criados = 0
    total_atualizados = 0

    for item in dados_spdata:
        spdata_atendimento_id = normalizar_int(item.get("SPDATA_ATENDIMENTO_ID"))
        data_hora_entrada = normalizar_datetime(item.get("DATA_HORA_ENTRADA"))
        paciente = normalizar_texto(item.get("PACIENTE"), 255)

        if not spdata_atendimento_id or not data_hora_entrada or not paciente:
            continue

        registro = existentes.get(spdata_atendimento_id)
        if registro is None:
            registro = MedSpdataAtendimento(
                spdata_atendimento_id=spdata_atendimento_id,
                data_hora_entrada=data_hora_entrada,
                data_atendimento=data_hora_entrada.date(),
                paciente=paciente,
            )
            db.session.add(registro)
            existentes[spdata_atendimento_id] = registro
            total_criados += 1
        else:
            total_atualizados += 1

        registro.cod_atendimento = normalizar_texto(item.get("COD_ATENDIMENTO"), 50)
        registro.id_paciente_spdata = normalizar_int(item.get("ID_PACIENTE_SPDATA"))
        registro.id_medico_spdata = normalizar_int(item.get("ID_MEDICO_SPDATA"))
        registro.medico = normalizar_texto(item.get("MEDICO"), 255)
        registro.crm_medico = normalizar_texto(item.get("CRM_MEDICO"), 50)
        registro.data_hora_entrada = data_hora_entrada
        registro.data_atendimento = data_hora_entrada.date()
        registro.hora_entrada = data_hora_entrada.time().replace(microsecond=0)
        registro.data_hora_alta_medica = normalizar_datetime(item.get("DATA_HORA_ALTA_MEDICA"))
        registro.id_convenio_spdata = normalizar_int(item.get("ID_CONVENIO_SPDATA"))
        registro.id_centro_custo_spdata = normalizar_int(item.get("ID_CENTRO_CUSTO_SPDATA"))
        registro.obs_atendimento = normalizar_texto(item.get("OBS_ATENDIMENTO"))
        registro.paciente = paciente
        registro.cpf = normalizar_cpf(item.get("CPF"))
        registro.prontuario = normalizar_texto(item.get("PRONTUARIO"), 50)
        registro.data_nascimento = normalizar_data(item.get("DATA_NASCIMENTO"))
        registro.sexo = normalizar_texto(item.get("SEXO"), 20)
        registro.celular = normalizar_texto(item.get("CELULAR"), 30)
        registro.email = normalizar_texto(item.get("EMAIL"), 255)
        registro.endereco = normalizar_texto(item.get("ENDERECO"), 500)
        registro.dados_spdata = item

    db.session.commit()

    return {
        "lidos": len(dados_spdata),
        "criados": total_criados,
        "atualizados": total_atualizados,
    }


def sexo_para_frontend(sexo):
    return "feminino" if str(sexo or "").upper().startswith("F") else "masculino"


def data_iso(valor):
    return valor.isoformat() if valor else None


def hora_hhmm(valor):
    return valor.strftime("%H:%M") if valor else ""


def data_hora_agenda(agenda):
    data_ref = agenda.data_agenda or date.today()
    hora_ref = agenda.hora_agenda or time.min
    return datetime.combine(data_ref, hora_ref)


def spdata_atendimento_id_placeholder(agenda):
    return -abs(int(agenda.spdata_agenda_id))


def crm_agenda(agenda):
    return normalizar_texto(agenda.crm_atend or agenda.crm, 50)


def status_agenda_spdata(agenda):
    atendido = normalizar_texto(agenda.atendido_spdata, 1)
    return "em-espera" if str(atendido or "").upper() == "S" else "agendado"


def atendimento_prioridade(atendimento):
    status = normalizar_status(atendimento.status if atendimento else None)
    if status == "faltou":
        return 3
    if status == "atendido":
        return 2
    if status == "em-atendimento":
        return 1
    return 0


def atendimento_join_agenda_cond():
    return or_(
        and_(
            MedAtendimentos.cod_atendimento.isnot(None),
            MedSpdataAgenda.registro.isnot(None),
            MedAtendimentos.cod_atendimento == MedSpdataAgenda.registro,
            MedAtendimentos.data_agenda == MedSpdataAgenda.data_agenda,
        ),
        and_(
            MedAtendimentos.cpf.isnot(None),
            MedSpdataAgenda.cpf.isnot(None),
            MedAtendimentos.cpf == MedSpdataAgenda.cpf,
            MedAtendimentos.data_agenda == MedSpdataAgenda.data_agenda,
            MedAtendimentos.hora_agenda == MedSpdataAgenda.hora_agenda,
        ),
    )


def agenda_keys(agenda):
    keys = set()
    registro = normalizar_texto(agenda.registro, 50)
    if registro:
        keys.add(("registro", registro))

    cpf = normalizar_texto(agenda.cpf, 20)
    if cpf and agenda.data_agenda and agenda.hora_agenda:
        keys.add(("cpf_data_hora", cpf, agenda.data_agenda, agenda.hora_agenda))

    return keys


def atendimento_matches_agenda(spdata, agenda):
    registro_spdata = normalizar_texto(spdata.cod_atendimento, 50)
    registro_agenda = normalizar_texto(agenda.registro, 50)
    if (
        registro_spdata
        and registro_agenda
        and registro_spdata == registro_agenda
        and spdata.data_atendimento == agenda.data_agenda
    ):
        return True

    cpf_spdata = normalizar_texto(spdata.cpf, 20)
    cpf_agenda = normalizar_texto(agenda.cpf, 20)
    return bool(
        cpf_spdata
        and cpf_agenda
        and cpf_spdata == cpf_agenda
        and spdata.data_atendimento == agenda.data_agenda
        and spdata.hora_entrada == agenda.hora_agenda
    )


def buscar_spdata_atendimento_para_agenda(agenda, atendimento=None):
    if atendimento and atendimento.med_spdata_atendimento_id:
        spdata = db.session.get(MedSpdataAtendimento, atendimento.med_spdata_atendimento_id)
        if spdata:
            return spdata

    registro = normalizar_texto(agenda.registro, 50)
    if registro:
        spdata = db.session.execute(
            select(MedSpdataAtendimento)
            .where(
                MedSpdataAtendimento.cod_atendimento == registro,
                MedSpdataAtendimento.data_atendimento == agenda.data_agenda,
            )
            .order_by(MedSpdataAtendimento.spdata_atendimento_id.desc())
        ).scalars().first()
        if spdata:
            return spdata

    cpf = normalizar_texto(agenda.cpf, 20)
    if cpf and agenda.data_agenda and agenda.hora_agenda:
        spdata = db.session.execute(
            select(MedSpdataAtendimento).where(
                MedSpdataAtendimento.cpf == cpf,
                MedSpdataAtendimento.data_atendimento == agenda.data_agenda,
                MedSpdataAtendimento.hora_entrada == agenda.hora_agenda,
            )
        ).scalars().first()
        if spdata:
            return spdata

    placeholder_id = spdata_atendimento_id_placeholder(agenda)
    spdata = db.session.execute(
        select(MedSpdataAtendimento).where(
            MedSpdataAtendimento.spdata_atendimento_id == placeholder_id
        )
    ).scalars().first()

    if spdata is None:
        spdata = MedSpdataAtendimento(
            spdata_atendimento_id=placeholder_id,
            data_hora_entrada=data_hora_agenda(agenda),
            data_atendimento=agenda.data_agenda,
            paciente=agenda.paciente,
        )
        db.session.add(spdata)

    spdata.cod_atendimento = registro
    spdata.id_paciente_spdata = agenda.id_paciente_spdata
    spdata.medico = agenda.medico
    spdata.crm_medico = crm_agenda(agenda)
    spdata.data_hora_entrada = data_hora_agenda(agenda)
    spdata.data_atendimento = agenda.data_agenda
    spdata.hora_entrada = agenda.hora_agenda
    spdata.id_convenio_spdata = agenda.id_convenio_spdata
    spdata.id_centro_custo_spdata = UNIDADE_PADRAO_SPDATA
    spdata.obs_atendimento = agenda.obs
    spdata.paciente = agenda.paciente
    spdata.cpf = agenda.cpf
    spdata.prontuario = agenda.prontuario
    spdata.data_nascimento = agenda.data_nascimento
    spdata.celular = agenda.celular or agenda.telefone
    spdata.email = agenda.email
    spdata.dados_spdata = agenda._to_dict()
    db.session.flush()

    return spdata


def buscar_atendimento_medsystem_para_spdata(spdata):
    atendimento = db.session.execute(
        select(MedAtendimentos).where(
            MedAtendimentos.med_spdata_atendimento_id == spdata.id
        )
    ).scalars().first()
    if atendimento:
        return atendimento

    filtros = []
    registro = normalizar_texto(spdata.cod_atendimento, 50)
    if registro and spdata.data_atendimento:
        filtros.append(and_(
            MedAtendimentos.cod_atendimento == registro,
            MedAtendimentos.data_agenda == spdata.data_atendimento,
        ))

    cpf = normalizar_texto(spdata.cpf, 20)
    if cpf and spdata.data_atendimento and spdata.hora_entrada:
        filtros.append(and_(
            MedAtendimentos.cpf == cpf,
            MedAtendimentos.data_agenda == spdata.data_atendimento,
            MedAtendimentos.hora_agenda == spdata.hora_entrada,
        ))

    if not filtros:
        return None

    atendimento = db.session.execute(
        select(MedAtendimentos)
        .where(or_(*filtros))
        .order_by(MedAtendimentos.id.desc())
    ).scalars().first()

    if atendimento:
        atendimento.med_spdata_atendimento_id = spdata.id
        atendimento.spdata_atendimento_id = spdata.spdata_atendimento_id

    return atendimento


def buscar_convenios_locais(codigos_spdata):
    codigos = [
        codigo
        for codigo in {normalizar_int(codigo) for codigo in codigos_spdata}
        if codigo is not None
    ]
    if not codigos:
        return {}

    registros = db.session.execute(
        select(MedSpdataConvenio).where(
            MedSpdataConvenio.codigo_spdata.in_(codigos)
        )
    ).scalars().all()

    return {
        registro.codigo_spdata: registro.nome
        for registro in registros
        if registro.nome
    }


def convenio_para_frontend(spdata, convenios_por_codigo=None):
    codigo = normalizar_int(spdata.id_convenio_spdata)
    if codigo is not None and convenios_por_codigo:
        nome = convenios_por_codigo.get(codigo)
        if nome:
            return nome

    dados_spdata = spdata.dados_spdata if isinstance(spdata.dados_spdata, dict) else {}
    nome_spdata = normalizar_texto(
        dados_spdata.get("CONVENIO_NOME") or dados_spdata.get("convenio"),
        255,
    )
    if nome_spdata:
        return nome_spdata

    return str(spdata.id_convenio_spdata or "")


def spdata_agenda_id_do_atendimento(spdata):
    dados_spdata = spdata.dados_spdata if isinstance(spdata.dados_spdata, dict) else {}
    return normalizar_int(
        dados_spdata.get("spdata_agenda_id") or dados_spdata.get("SPDATA_AGENDA_ID")
    )


def agenda_para_frontend(spdata, atendimento=None, convenios_por_codigo=None):
    status = normalizar_status(atendimento.status) if atendimento else "em-espera"
    data_atendimento = data_iso(spdata.data_atendimento)
    horario = hora_hhmm(spdata.hora_entrada)
    paciente_id = spdata.id_paciente_spdata or spdata.id
    id_convenio_spdata = normalizar_int(spdata.id_convenio_spdata)

    return {
        "id": spdata.id,
        "spdataAtendimentoId": spdata.spdata_atendimento_id,
        "codAtendimento": spdata.cod_atendimento,
        "medsystemAtendimentoId": atendimento.id if atendimento else None,
        "pacienteId": paciente_id,
        "medicoId": spdata.id_medico_spdata or 0,
        "clinicaId": 1,
        "data": data_atendimento,
        "horario": horario,
        "prioridade": "normal",
        "status": status,
        "descricao": spdata.obs_atendimento or "",
        "criadoEm": spdata.data_hora_entrada.isoformat() if spdata.data_hora_entrada else None,
        "paciente": {
            "id": paciente_id,
            "nome": spdata.paciente,
            "encaixado": False,
            "sexo": sexo_para_frontend(spdata.sexo),
            "dataNascimento": data_iso(spdata.data_nascimento) or "1900-01-01",
            "tipoSanguineo": "",
            "alergias": [],
            "medicamentosEmUso": [],
            "convenio": convenio_para_frontend(spdata, convenios_por_codigo),
            "idConvenioSpdata": id_convenio_spdata,
            "telefone": spdata.celular or "",
            "email": spdata.email or "Não Informado",
            "cpf": spdata.cpf or "",
            "endereco": spdata.endereco or "",
            "historicoRecente": [],
        },
    }


def agenda_spdata_para_frontend(agenda, spdata_ref, atendimento=None, convenios_por_codigo=None):
    status = normalizar_status(atendimento.status) if atendimento else status_agenda_spdata(agenda)
    id_convenio_spdata = normalizar_int(agenda.id_convenio_spdata)
    paciente_id = agenda.id_paciente_spdata or agenda.id
    telefone = agenda.celular or agenda.telefone or ""

    if id_convenio_spdata is not None and convenios_por_codigo:
        convenio = convenios_por_codigo.get(id_convenio_spdata) or agenda.convenio or ""
    else:
        convenio = agenda.convenio or ""

    return {
        "id": spdata_ref.id,
        "spdataAtendimentoId": spdata_ref.spdata_atendimento_id,
        "spdataAgendaId": agenda.spdata_agenda_id,
        "agendaId": agenda.id,
        "codAtendimento": agenda.registro,
        "medsystemAtendimentoId": atendimento.id if atendimento else None,
        "pacienteId": paciente_id,
        "medicoId": spdata_ref.id_medico_spdata or 0,
        "clinicaId": 1,
        "data": data_iso(agenda.data_agenda),
        "horario": hora_hhmm(agenda.hora_agenda),
        "prioridade": "normal",
        "status": status,
        "descricao": agenda.obs or "",
        "criadoEm": data_hora_agenda(agenda).isoformat(),
        "paciente": {
            "id": paciente_id,
            "nome": agenda.paciente,
            "encaixado": False,
            "sexo": "masculino",
            "dataNascimento": data_iso(agenda.data_nascimento) or "1900-01-01",
            "tipoSanguineo": "",
            "alergias": [],
            "medicamentosEmUso": [],
            "convenio": convenio,
            "idConvenioSpdata": id_convenio_spdata,
            "telefone": telefone,
            "email": agenda.email or "Não Informado",
            "cpf": agenda.cpf or "",
            "endereco": "",
            "historicoRecente": [],
        },
    }


def listar_atendimentos_medsystem_para_frontend(crm_medico, data_ini=None, data_fim=None, status=None, search=None):
    filtros = [
        MedSpdataAtendimento.crm_medico == crm_medico,
        or_(
            MedSpdataAtendimento.id_centro_custo_spdata == UNIDADE_PADRAO_SPDATA,
            MedSpdataAtendimento.id_centro_custo_spdata.is_(None),
        ),
    ]

    if data_ini:
        filtros.append(MedAtendimentos.data_agenda >= data_ini)
    if data_fim:
        filtros.append(MedAtendimentos.data_agenda <= data_fim)
    if status:
        filtros.append(MedAtendimentos.status.in_(valores_status_medsystem(status)))

    termo = normalizar_texto(search, 255)
    if termo:
        like = f"%{termo}%"
        filtros.append(or_(
            MedAtendimentos.paciente.ilike(like),
            MedSpdataAtendimento.paciente.ilike(like),
        ))

    registros = (
        db.session.query(MedSpdataAtendimento, MedAtendimentos)
        .join(
            MedAtendimentos,
            MedAtendimentos.med_spdata_atendimento_id == MedSpdataAtendimento.id,
        )
        .filter(*filtros)
        .order_by(MedAtendimentos.data_agenda.desc(), MedAtendimentos.hora_agenda.desc(), MedAtendimentos.paciente)
        .all()
    )

    convenios_por_codigo = buscar_convenios_locais(
        spdata.id_convenio_spdata for spdata, _ in registros
    )

    return [
        agenda_para_frontend(spdata, atendimento, convenios_por_codigo)
        for spdata, atendimento in registros
    ]


def listar_agenda_medica(usuario_id, data_ini, data_fim, status=None, search=None):
    crm_medico = get_crm_medico_usuario(usuario_id)
    status = normalizar_status(status)
    if status and status not in STATUS_VALIDOS:
        raise ValueError("Status inválido")

    search = normalizar_texto(search, 255)

    if data_ini is None and data_fim is None:
        return listar_atendimentos_medsystem_para_frontend(
            crm_medico,
            status=status,
            search=search,
        )

    if data_fim < data_ini:
        raise ValueError("dataFim não pode ser menor que dataIni.")

    sincronizar_agenda_spdata(data_ini, data_fim)
    sincronizar_atendimentos_spdata(data_ini, data_fim, crm_medico)

    rows_agenda = (
        db.session.query(MedSpdataAgenda, MedAtendimentos)
        .outerjoin(MedAtendimentos, atendimento_join_agenda_cond())
        .filter(
            MedSpdataAgenda.data_agenda >= data_ini,
            MedSpdataAgenda.data_agenda <= data_fim,
            or_(
                MedSpdataAgenda.crm_atend == crm_medico,
                MedSpdataAgenda.crm == crm_medico,
            ),
        )
        .order_by(MedSpdataAgenda.data_agenda, MedSpdataAgenda.hora_agenda, MedSpdataAgenda.paciente)
        .all()
    )

    agendas_por_id = {}
    for agenda, atendimento in rows_agenda:
        atual = agendas_por_id.get(agenda.id)
        if atual is None or atendimento_prioridade(atendimento) > atendimento_prioridade(atual[1]):
            agendas_por_id[agenda.id] = (agenda, atendimento)

    convenios_por_codigo = buscar_convenios_locais(
        agenda.id_convenio_spdata
        for agenda, _ in agendas_por_id.values()
    )

    items = []
    agendas_encontradas = []
    for agenda, atendimento in agendas_por_id.values():
        spdata_ref = buscar_spdata_atendimento_para_agenda(agenda, atendimento)
        items.append(agenda_spdata_para_frontend(agenda, spdata_ref, atendimento, convenios_por_codigo))
        agendas_encontradas.append(agenda)

    chaves_agenda = {
        chave
        for agenda in agendas_encontradas
        for chave in agenda_keys(agenda)
    }

    registros = (
        db.session.query(MedSpdataAtendimento, MedAtendimentos)
        .outerjoin(
            MedAtendimentos,
            MedAtendimentos.med_spdata_atendimento_id == MedSpdataAtendimento.id,
        )
        .filter(
            MedSpdataAtendimento.data_atendimento >= data_ini,
            MedSpdataAtendimento.data_atendimento <= data_fim,
            MedSpdataAtendimento.crm_medico == crm_medico,
            MedSpdataAtendimento.id_centro_custo_spdata == UNIDADE_PADRAO_SPDATA,
        )
        .order_by(MedSpdataAtendimento.data_hora_entrada, MedSpdataAtendimento.paciente)
        .all()
    )

    convenios_atendimento = buscar_convenios_locais(
        spdata.id_convenio_spdata for spdata, _ in registros
    )

    for spdata, atendimento in registros:
        registro = normalizar_texto(spdata.cod_atendimento, 50)
        cpf = normalizar_texto(spdata.cpf, 20)
        chaves_spdata = set()
        if registro:
            chaves_spdata.add(("registro", registro))
        if cpf and spdata.data_atendimento and spdata.hora_entrada:
            chaves_spdata.add(("cpf_data_hora", cpf, spdata.data_atendimento, spdata.hora_entrada))

        if chaves_spdata & chaves_agenda:
            continue

        if any(atendimento_matches_agenda(spdata, agenda) for agenda in agendas_encontradas):
            continue

        items.append(agenda_para_frontend(spdata, atendimento, convenios_atendimento))

    db.session.commit()

    items = filtrar_agenda_frontend(items, status=status, search=search)

    return sorted(items, key=lambda item: (item.get("data") or "", item.get("horario") or "", item["paciente"]["nome"] or ""))


def linhas_texto(valor):
    if not valor:
        return []

    linhas = []
    for linha in str(valor).splitlines():
        texto = linha.strip().lstrip("•- ").strip()
        if texto:
            linhas.append(texto)

    return linhas


def normalizar_exame_id(valor):
    if valor is None or valor == "":
        return None

    try:
        exame_id = int(valor)
    except (TypeError, ValueError):
        raise ValueError("exame_id inválido")

    if exame_id <= 0:
        raise ValueError("exame_id inválido")

    return exame_id


def normalizar_exames_consulta(valor):
    if valor is None or valor == "":
        return []

    itens = [valor] if isinstance(valor, dict) else valor
    if isinstance(valor, str):
        itens = linhas_texto(valor)
    elif not isinstance(itens, (list, tuple)):
        itens = [itens]

    exames = []
    exame_ids = set()

    for item in itens:
        if isinstance(item, dict):
            if "exame_id" in item:
                exame_id_raw = item.get("exame_id")
            elif "exameId" in item:
                exame_id_raw = item.get("exameId")
            else:
                exame_id_raw = item.get("id")

            exame_id = normalizar_exame_id(exame_id_raw)
            nome = normalizar_texto(
                item.get("nome")
                or item.get("nome_exame")
                or item.get("tipo_exame")
                or item.get("descricao")
                or item.get("label"),
                255,
            )
            descricao = normalizar_texto(
                item.get("descricao")
                or item.get("nome")
                or item.get("nome_exame")
                or item.get("tipo_exame")
                or item.get("label")
            )
            justificativa = normalizar_texto(item.get("justificativa"))
            orientacao = normalizar_texto(item.get("orientacao") or item.get("orientacoes"))
        else:
            exame_id = None
            nome = normalizar_texto(item, 255)
            descricao = normalizar_texto(item)
            justificativa = None
            orientacao = None

        if not nome and not exame_id:
            continue

        if exame_id:
            exame_ids.add(exame_id)

        exames.append({
            "nome": nome,
            "exame_id": exame_id,
            "descricao": descricao,
            "justificativa": justificativa,
            "orientacao": orientacao,
        })

    exames_por_id = {}
    if exame_ids:
        exames_por_id = {
            exame.id: exame
            for exame in db.session.execute(
                select(Exame).where(Exame.id.in_(exame_ids))
            ).scalars()
        }
        ids_inexistentes = sorted(exame_ids - set(exames_por_id.keys()))
        if ids_inexistentes:
            raise ValueError(
                f"exame_id inválido: {', '.join(str(i) for i in ids_inexistentes)}"
            )

    normalizados = []
    for item in exames:
        exame = exames_por_id.get(item["exame_id"])
        nome = item["nome"] or (exame.nome if exame else None)
        if not nome:
            continue

        normalizados.append({
            "nome": normalizar_texto(nome, 255) or nome[:255],
            "exame_id": item["exame_id"],
            "descricao": item["descricao"] or nome,
            "justificativa": item["justificativa"],
            "orientacao": item["orientacao"],
        })

    return normalizados


def normalizar_diagnosticos_consulta(consulta):
    if "diagnosticos" in consulta:
        valor = consulta.get("diagnosticos")
    elif "diagnostico" in consulta:
        valor = consulta.get("diagnostico")
    else:
        return None

    if not valor:
        return []

    if isinstance(valor, dict):
        itens = [valor]
    elif isinstance(valor, str):
        itens = linhas_texto(valor)
    elif isinstance(valor, (list, tuple)):
        itens = valor
    else:
        itens = [valor]

    diagnosticos = []
    codigos_usados = set()

    for item in itens:
        if isinstance(item, dict):
            cid_codigo = normalizar_texto(
                item.get("cid")
                or item.get("cid_codigo")
                or item.get("codigo")
                or item.get("value"),
                20,
            )
            cid_descricao = normalizar_texto(
                item.get("nome")
                or item.get("cid_descricao")
                or item.get("descricao")
                or item.get("label"),
                255,
            )
            diagnostico_descritivo = normalizar_texto(
                item.get("diagnostico_descritivo") or cid_descricao or cid_codigo
            )
        else:
            texto = normalizar_texto(item, 255)
            if not texto:
                continue

            cid_codigo, separador, cid_descricao = texto.partition("—")
            if not separador:
                cid_codigo, separador, cid_descricao = texto.partition(" - ")

            cid_codigo = normalizar_texto(cid_codigo, 20)
            cid_descricao = normalizar_texto(cid_descricao, 255) if separador else None
            diagnostico_descritivo = texto

        if not cid_codigo:
            continue

        codigo_chave = cid_codigo.upper()
        if codigo_chave in codigos_usados:
            continue

        codigos_usados.add(codigo_chave)
        diagnosticos.append(
            {
                "cid_codigo": cid_codigo,
                "cid_descricao": cid_descricao,
                "diagnostico_descritivo": diagnostico_descritivo,
            }
        )

    return diagnosticos


def salvar_conteudo_clinico(spdata, atendimento_medsystem, usuario_id, consulta):
    if not consulta:
        return

    exames_consulta = None
    if "exames" in consulta:
        exames_consulta = normalizar_exames_consulta(consulta.get("exames"))

    spdata_agenda_id = spdata_agenda_id_do_atendimento(spdata)

    filtros_atendimento = [Atendimento.spdata_atendimento_id == spdata.spdata_atendimento_id]
    if spdata_agenda_id is not None:
        filtros_atendimento.append(Atendimento.spdata_agenda_id == spdata_agenda_id)

    atendimento = db.session.execute(
        select(Atendimento).where(or_(*filtros_atendimento))
    ).scalars().first()

    hora_inicio = (
        atendimento_medsystem.started_at.time().replace(microsecond=0)
        if atendimento_medsystem.started_at
        else spdata.hora_entrada
    )
    hora_fim = datetime.utcnow().time().replace(microsecond=0)

    if atendimento is None:
        atendimento = Atendimento(
            spdata_paciente_id=spdata.id_paciente_spdata,
            spdata_agenda_id=spdata_agenda_id,
            spdata_medico_id=spdata.id_medico_spdata,
            paciente_nome=spdata.paciente,
            paciente_cpf=spdata.cpf or "",
            data_atendimento=spdata.data_hora_entrada,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            spdata_atendimento_id=spdata.spdata_atendimento_id,
        )
        db.session.add(atendimento)
        db.session.flush()
        atendimento.status = "finalizado"
    else:
        atendimento.hora_fim = hora_fim
        atendimento.status = "finalizado"

    anamnese_texto = normalizar_texto(consulta.get("anamnese"))
    if anamnese_texto:
        if atendimento.anamnese:
            atendimento.anamnese.observacoes = anamnese_texto
        else:
            db.session.add(Anamnese(atendimento_id=atendimento.id, observacoes=anamnese_texto))

        evolucao = atendimento.evolucoes_medicas[0] if atendimento.evolucoes_medicas else None
        if evolucao:
            evolucao.texto_evolucao = anamnese_texto
            evolucao.status = "finalizado"
        else:
            db.session.add(
                EvolucaoMedica(
                    atendimento_id=atendimento.id,
                    medico_id=usuario_id,
                    texto_evolucao=anamnese_texto,
                    status="finalizado",
                )
            )

    diagnosticos = normalizar_diagnosticos_consulta(consulta)
    if diagnosticos is not None:
        for diagnostico_existente in list(atendimento.diagnosticos):
            db.session.delete(diagnostico_existente)

        for indice, diagnostico in enumerate(diagnosticos):
            db.session.add(
                Diagnostico(
                    atendimento_id=atendimento.id,
                    cid_codigo=diagnostico["cid_codigo"],
                    cid_descricao=diagnostico["cid_descricao"],
                    diagnostico_descritivo=diagnostico["diagnostico_descritivo"],
                    principal=indice == 0,
                )
            )

    if "medicamentos" in consulta:
        for prescricao in list(atendimento.prescricoes):
            db.session.delete(prescricao)

        for linha in linhas_texto(consulta.get("medicamentos")):
            nome, separador, dosagem = linha.partition("—")
            db.session.add(
                Prescricao(
                    atendimento_id=atendimento.id,
                    medico_id=usuario_id,
                    medicamento=normalizar_texto(nome, 255) or linha[:255],
                    dosagem=normalizar_texto(dosagem, 100) if separador else None,
                    orientacoes=linha,
                )
            )

    if "exames" in consulta:
        for solicitacao in list(atendimento.solicitacoes_exames):
            db.session.delete(solicitacao)

        for exame in exames_consulta:
            db.session.add(
                SolicitacaoExame(
                    atendimento_id=atendimento.id,
                    tipo_exame=exame["nome"],
                    exame_id=exame["exame_id"],
                    descricao=exame["descricao"],
                    justificativa=exame["justificativa"],
                    orientacao=exame["orientacao"],
                )
            )


def atualizar_status_agenda(med_spdata_atendimento_id, status, usuario_id=None, consulta=None):
    status = normalizar_status(status)
    if status not in STATUS_VALIDOS:
        raise ValueError("Status inválido")

    if usuario_id is None:
        raise PermissionError("Usuário autenticado obrigatório")

    spdata = db.session.get(MedSpdataAtendimento, med_spdata_atendimento_id)
    if not spdata:
        raise LookupError("Atendimento do SPDATA não encontrado no MedSystem")

    crm_medico_usuario = get_crm_medico_usuario(usuario_id)
    if normalizar_texto(spdata.crm_medico, 50) != crm_medico_usuario:
        raise PermissionError("Atendimento não pertence ao médico autenticado")

    atendimento = buscar_atendimento_medsystem_para_spdata(spdata)

    if atendimento is None:
        atendimento = MedAtendimentos(
            med_spdata_atendimento_id=spdata.id,
            spdata_atendimento_id=spdata.spdata_atendimento_id,
            cod_atendimento=spdata.cod_atendimento,
            data_agenda=spdata.data_atendimento,
            hora_agenda=spdata.hora_entrada,
            id_medico_spdata=spdata.id_medico_spdata,
            medico=spdata.medico,
            id_paciente_spdata=spdata.id_paciente_spdata,
            paciente=spdata.paciente,
            cpf=spdata.cpf,
            prontuario=spdata.prontuario,
        )
        db.session.add(atendimento)

    if status == "em-atendimento":
        atendimento.marcar_em_atendimento()
    elif status == "atendido":
        atendimento.marcar_atendido()
        salvar_conteudo_clinico(spdata, atendimento, usuario_id, consulta)
    elif status == "faltou":
        atendimento.marcar_faltou()

    db.session.commit()
    convenios_por_codigo = buscar_convenios_locais([spdata.id_convenio_spdata])

    spdata_agenda_id = spdata_agenda_id_do_atendimento(spdata)
    if spdata_agenda_id is not None:
        agenda = db.session.execute(
            select(MedSpdataAgenda).where(
                MedSpdataAgenda.spdata_agenda_id == spdata_agenda_id
            )
        ).scalars().first()
        if agenda:
            return agenda_spdata_para_frontend(agenda, spdata, atendimento, convenios_por_codigo)

    return agenda_para_frontend(spdata, atendimento, convenios_por_codigo)
