from collections import Counter
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, or_, select

from src.models.medico_model import Medico
from src.models.model_mydsystem.med_atendimentos_model import MedAtendimentos
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.services.spdata_agenda_service import sincronizar_agenda_spdata
from src.settings.extensions import db


STATUS_MEDSYSTEM_ALIASES = {
    "EM_ATENDIMENTO": "em-atendimento",
    "em_atendimento": "em-atendimento",
    "em-atendimento": "em-atendimento",
    "ATENDIDO": "atendido",
    "atendido": "atendido",
    "FALTOU": "faltou",
    "faltou": "faltou",
}

STATUS_NO_SHOW = {"faltou", "nao-confirmado"}
MOTIVOS_NO_SHOW = {"esquecimento", "transporte", "outros"}

NO_SHOW_GRACE_PERIOD = timedelta(hours=8)


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


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


def normalizar_status_medsystem(status):
    return STATUS_MEDSYSTEM_ALIASES.get(normalizar_texto(status))


def normalizar_motivo_no_show(motivo):
    motivo = normalizar_texto(motivo)
    if motivo not in MOTIVOS_NO_SHOW:
        return None
    return motivo


def data_iso(valor):
    return valor.isoformat() if valor else ""


def hora_hhmm(valor):
    return valor.strftime("%H:%M") if valor else ""


def consulta_ja_venceu(agenda, agora=None):
    agora = agora or datetime.now()

    if not agenda.hora_agenda:
        return agenda.data_agenda < agora.date()

    horario_limite = datetime.combine(agenda.data_agenda, agenda.hora_agenda) + NO_SHOW_GRACE_PERIOD
    return horario_limite <= agora


def situacao_no_show(agenda, atendimento=None, agora=None):
    status_medsystem = normalizar_status_medsystem(atendimento.status if atendimento else None)
    if status_medsystem == "faltou":
        return "faltou", "medico_marcou_faltou"

    if atendimento is not None:
        return None, None

    if normalizar_texto(agenda.atendido_spdata).upper() == "N" and consulta_ja_venceu(agenda, agora):
        return "nao-confirmado", "nao_compareceu_recepcao"

    return None, None


def atendimento_prioridade(atendimento):
    status = normalizar_status_medsystem(atendimento.status if atendimento else None)
    if status == "faltou":
        return 3
    if status == "atendido":
        return 2
    if status == "em-atendimento":
        return 1
    return 0


def buscar_especialidades_medicos_locais(agendas):
    chaves = sorted({
        chave
        for agenda in agendas
        for chave in (
            normalizar_identificador_medico(agenda.crm_atend),
            normalizar_identificador_medico(agenda.crm),
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


def especialidade_agenda(agenda, especialidades_por_medico):
    for chave in (
        normalizar_identificador_medico(agenda.crm_atend),
        normalizar_identificador_medico(agenda.crm),
    ):
        especialidade = especialidades_por_medico.get(chave)
        if especialidade:
            return especialidade

    return normalizar_especialidade(agenda.especialidade)


def montar_item(agenda, atendimento, status, situacao, especialidades_por_medico):
    telefone = normalizar_texto(agenda.celular) or normalizar_texto(agenda.telefone)
    return {
        "id": agenda.id,
        "clinicaId": agenda.unidade_id,
        "unidadeId": agenda.unidade_id,
        "spdataAgendaId": agenda.spdata_agenda_id,
        "medsystemAtendimentoId": atendimento.id if atendimento else None,
        "nome": normalizar_texto(agenda.paciente),
        "telefone": telefone,
        "convenio": normalizar_texto(agenda.convenio),
        "medico": normalizar_texto(agenda.medico),
        "especialidade": especialidade_agenda(agenda, especialidades_por_medico),
        "dataFalta": data_iso(agenda.data_agenda),
        "horario": hora_hhmm(agenda.hora_agenda),
        "status": status,
        "situacao": situacao,
        "motivo": normalizar_motivo_no_show(getattr(agenda, "motivo_no_show", None)),
        "recuperado": False,
        "cpf": normalizar_texto(agenda.cpf),
        "prontuario": normalizar_texto(agenda.prontuario),
    }


def registrar_motivo_no_show(agenda_id, motivo):
    motivo_normalizado = normalizar_motivo_no_show(motivo)
    if not motivo_normalizado:
        raise ValueError("Motivo do no-show inválido")

    agenda = db.session.get(MedSpdataAgenda, agenda_id)
    if not agenda:
        raise LookupError("Agenda do no-show não encontrada")

    agenda.motivo_no_show = motivo_normalizado
    db.session.commit()

    return {
        "id": agenda.id,
        "motivo": agenda.motivo_no_show,
    }


def filtro_texto(item, termo):
    if not termo:
        return True
    texto = " ".join([
        item["nome"],
        item["telefone"],
        item["cpf"],
        item["prontuario"],
        item["medico"],
    ]).casefold()
    return termo.casefold() in texto


def aplicar_filtros(items, medico=None, especialidade=None, convenio=None, status=None, q=None):
    medico = normalizar_texto(medico)
    especialidade = normalizar_texto(especialidade)
    convenio = normalizar_texto(convenio)
    status = normalizar_texto(status)
    q = normalizar_texto(q)

    return [
        item
        for item in items
        if (not medico or medico == "Todos" or item["medico"] == medico)
        and (not especialidade or especialidade == "Todos" or item["especialidade"] == especialidade)
        and (not convenio or convenio == "Todos" or item["convenio"] == convenio)
        and (not status or status == "Todos" or item["status"] == status)
        and filtro_texto(item, q)
    ]


def opcoes(items, campo):
    return sorted({normalizar_texto(item[campo]) for item in items if normalizar_texto(item[campo])})


def opcoes_especialidades(items):
    return sorted({
        especialidade
        for item in items
        if (especialidade := normalizar_especialidade(item["especialidade"]))
    })


def grafico_por_mes(items):
    contador = Counter(item["dataFalta"][:7] for item in items if item["dataFalta"])
    return [
        {"label": label, "total": total}
        for label, total in sorted(contador.items())
    ]


def grafico_por_especialidade(items):
    contador = Counter(item["especialidade"] or "Não informada" for item in items)
    return [
        {"label": label, "total": total}
        for label, total in sorted(contador.items())
    ]


def grafico_por_dia_semana(items):
    labels = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    totais = {label: 0 for label in labels}
    for item in items:
        if not item["dataFalta"]:
            continue
        dia = datetime.fromisoformat(item["dataFalta"]).weekday()
        label = labels[(dia + 1) % 7]
        totais[label] += 1

    return [
        {"label": label, "total": total}
        for label, total in totais.items()
    ]


def resumo(items):
    return {
        "totalResgate": len(items),
        "faltou": sum(1 for item in items if item["status"] == "faltou"),
        "naoConfirmado": sum(1 for item in items if item["status"] == "nao-confirmado"),
        "recuperados": sum(1 for item in items if item["recuperado"]),
        "semContato": 0,
    }


def listar_no_show(
    data_ini,
    data_fim,
    unidade,
    medico=None,
    especialidade=None,
    convenio=None,
    status=None,
    q=None,
    page=1,
    page_size=20,
):
    if data_fim < data_ini:
        raise ValueError("dataFim não pode ser menor que dataIni.")

    sincronizar_agenda_spdata(data_ini, data_fim, unidade=unidade)

    mesma_unidade = or_(
        MedAtendimentos.unidade_id == MedSpdataAgenda.unidade_id,
        MedAtendimentos.unidade_id.is_(None),
        MedSpdataAgenda.unidade_id.is_(None),
    )
    join_cond = and_(
        mesma_unidade,
        or_(
            and_(
                MedAtendimentos.cod_atendimento.isnot(None),
                MedSpdataAgenda.registro.isnot(None),
                MedAtendimentos.cod_atendimento == MedSpdataAgenda.registro,
            ),
            and_(
                MedAtendimentos.cpf.isnot(None),
                MedSpdataAgenda.cpf.isnot(None),
                MedAtendimentos.cpf == MedSpdataAgenda.cpf,
                MedAtendimentos.data_agenda == MedSpdataAgenda.data_agenda,
                MedAtendimentos.hora_agenda == MedSpdataAgenda.hora_agenda,
            ),
        ),
    )

    rows = (
        db.session.query(MedSpdataAgenda, MedAtendimentos)
        .outerjoin(MedAtendimentos, join_cond)
        .filter(
            MedSpdataAgenda.data_agenda >= data_ini,
            MedSpdataAgenda.data_agenda <= data_fim,
            MedSpdataAgenda.unidade_id == unidade.id,
        )
        .order_by(MedSpdataAgenda.data_agenda, MedSpdataAgenda.hora_agenda, MedSpdataAgenda.paciente)
        .all()
    )

    por_agenda = {}
    for agenda, atendimento in rows:
        atual = por_agenda.get(agenda.id)
        if atual is None or atendimento_prioridade(atendimento) > atendimento_prioridade(atual[1]):
            por_agenda[agenda.id] = (agenda, atendimento)

    agora = datetime.now()
    items_periodo = []
    especialidades_por_medico = buscar_especialidades_medicos_locais(
        agenda
        for agenda, _ in por_agenda.values()
    )

    for agenda, atendimento in por_agenda.values():
        status_item, situacao = situacao_no_show(agenda, atendimento, agora)
        if status_item not in STATUS_NO_SHOW:
            continue
        items_periodo.append(
            montar_item(agenda, atendimento, status_item, situacao, especialidades_por_medico)
        )

    items_filtrados = aplicar_filtros(
        items_periodo,
        medico=medico,
        especialidade=especialidade,
        convenio=convenio,
        status=status,
        q=q,
    )

    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 20), 1), 500)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items_filtrados[start:end],
        "total": len(items_filtrados),
        "page": page,
        "pageSize": page_size,
        "resumo": resumo(items_filtrados),
        "filtros": {
            "medicos": opcoes(items_periodo, "medico"),
            "especialidades": opcoes_especialidades(items_periodo),
            "convenios": opcoes(items_periodo, "convenio"),
            "anos": sorted({item["dataFalta"][:4] for item in items_periodo if item["dataFalta"]}),
        },
        "graficos": {
            "porMes": grafico_por_mes(items_filtrados),
            "porEspecialidade": grafico_por_especialidade(items_filtrados),
            "porDiaSemana": grafico_por_dia_semana(items_filtrados),
        },
    }
