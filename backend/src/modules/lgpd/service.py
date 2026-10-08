import re
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.models.auditoria_model import Auditoria
from src.models.documento_personalizado_model import DocumentoPersonalizado
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.models.model_mydsystem.med_spdata_atendimentos_model import (
    MedSpdataAtendimento,
)
from src.services.auditoria_service import registrar_auditoria
from src.services.retencao_exames_service import listar_retencao_exames
from src.settings.extensions import db


PACIENTE_ID_DESCRICAO_RE = re.compile(r"(?:^|[;\s])paciente_id=(\d+)")
STATUS_DESCRICAO_RE = re.compile(r"(?:^|[;\s])status=([^;\s]+)")
ENTIDADES_PACIENTE_DIRETAS = {"paciente", "paciente_spdata"}
ENTIDADES_ATENDIMENTO_SPDATA = {"agenda_medica", "med_spdata_atendimentos"}
ENTIDADES_AGENDA_SPDATA = {"agenda_assistente"}
DESCRICOES_INTERACAO_PACIENTE = {
    "INICIOU_ATENDIMENTO": "Médico iniciou o atendimento do paciente.",
    "FINALIZOU_ATENDIMENTO": "Médico finalizou o atendimento do paciente.",
    "ABRIU_PACIENTE": "Médico abriu os dados do paciente.",
    "VISUALIZOU_PRONTUARIO": "Médico visualizou o histórico local do paciente.",
    "VISUALIZOU_HISTORICO_BIODATA": "Médico consultou o histórico BioData do paciente.",
    "VISUALIZOU_HISTORICO_SPDATA": "Médico consultou o histórico SPDATA do paciente.",
    "VISUALIZOU_EXAMES_PACS": "Médico visualizou exames PACS do paciente.",
    "VISUALIZOU_LAUDO_EXAME": "Médico abriu laudo de exame do paciente.",
    "VISUALIZOU_IMAGEM_EXAME": "Médico abriu imagem de exame do paciente.",
    "VISUALIZOU_DOCUMENTOS_MEDICOS": "Médico visualizou documentos médicos do paciente.",
    "SALVOU_DOCUMENTO_MEDICO": "Médico salvou documento médico do paciente.",
    "EDITOU_EVOLUCAO": "Médico editou a evolução clínica do paciente.",
}


def parse_data(valor, default=None):
    if not valor:
        return default

    return datetime.fromisoformat(str(valor)[:10]).date()


def _timezone_auditoria():
    try:
        return ZoneInfo(current_app.config.get("AUDITORIA_TIMEZONE", "America/Sao_Paulo"))
    except ZoneInfoNotFoundError:
        return ZoneInfo("America/Sao_Paulo")


def _data_local_para_utc_sem_timezone(data, horario):
    local = datetime.combine(data, horario).replace(tzinfo=_timezone_auditoria())
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def _normalizar_int(valor):
    try:
        return int(valor) if valor not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _texto(valor):
    texto = str(valor or "").strip()
    return texto or None


def _paciente_payload(paciente_id=None, nome=None, nome_social=None):
    paciente_id = _normalizar_int(paciente_id)
    nome = _texto(nome)
    nome_social = _texto(nome_social)
    if paciente_id is None and not nome and not nome_social:
        return None

    label = nome_social or nome or f"Paciente #{paciente_id}"
    return {
        "id": paciente_id,
        "nome": nome,
        "nome_social": nome_social,
        "label": label,
    }


def _paciente_de_atendimento_spdata(spdata):
    return _paciente_payload(
        paciente_id=(
            getattr(spdata, "id_paciente_spdata", None)
            or getattr(spdata, "id", None)
        ),
        nome=getattr(spdata, "paciente", None),
        nome_social=getattr(spdata, "paciente_nome_social", None),
    )


def _paciente_de_agenda_spdata(agenda):
    return _paciente_payload(
        paciente_id=(
            getattr(agenda, "id_paciente_spdata", None)
            or getattr(agenda, "id", None)
        ),
        nome=getattr(agenda, "paciente", None),
        nome_social=getattr(agenda, "paciente_nome_social", None),
    )


def _paciente_de_atendimento_local(atendimento):
    return _paciente_payload(
        paciente_id=getattr(atendimento, "spdata_paciente_id", None),
        nome=getattr(atendimento, "paciente_nome", None),
    )


def _paciente_id_descricao(descricao):
    match = PACIENTE_ID_DESCRICAO_RE.search(str(descricao or ""))
    return _normalizar_int(match.group(1)) if match else None


def _status_descricao(descricao):
    match = STATUS_DESCRICAO_RE.search(str(descricao or ""))
    if not match:
        return None
    return match.group(1).replace("-", " ")


def _paciente_id_direto_evento(evento):
    entidade_id = _normalizar_int(evento.entidade_id)
    paciente_id = _paciente_id_descricao(evento.descricao)
    if paciente_id is not None:
        return paciente_id
    if evento.entidade in ENTIDADES_PACIENTE_DIRETAS:
        return entidade_id
    if evento.entidade == "exame_pacs" and evento.acao == "VISUALIZOU_EXAMES_PACS":
        return entidade_id
    return None


def _set_por_ids(modelo, ids):
    ids = {item for item in ids if item is not None}
    if not ids:
        return []
    return db.session.execute(select(modelo).where(modelo.id.in_(ids))).scalars().all()


def _mapear_pacientes_auditoria(eventos):
    pacientes_ids = set()
    atendimentos_ids = set()
    agendas_ids = set()
    documentos_personalizados_ids = set()

    for evento in eventos:
        entidade_id = _normalizar_int(evento.entidade_id)
        paciente_id = _paciente_id_direto_evento(evento)
        if paciente_id is not None:
            pacientes_ids.add(paciente_id)
        if entidade_id is not None and evento.entidade in ENTIDADES_ATENDIMENTO_SPDATA:
            atendimentos_ids.add(entidade_id)
        if entidade_id is not None and evento.entidade in ENTIDADES_AGENDA_SPDATA:
            agendas_ids.add(entidade_id)
        if (
            entidade_id is not None
            and evento.entidade == "documentos_medicos_personalizados"
        ):
            documentos_personalizados_ids.add(entidade_id)

    atendimentos_por_id = {
        item.id: _paciente_de_atendimento_spdata(item)
        for item in _set_por_ids(MedSpdataAtendimento, atendimentos_ids)
    }
    agendas_por_id = {
        item.id: _paciente_de_agenda_spdata(item)
        for item in _set_por_ids(MedSpdataAgenda, agendas_ids)
    }

    pacientes_por_spdata_id = {}
    if pacientes_ids:
        atendimentos_paciente = db.session.execute(
            select(MedSpdataAtendimento).where(
                MedSpdataAtendimento.id_paciente_spdata.in_(pacientes_ids)
            )
        ).scalars().all()
        for atendimento in atendimentos_paciente:
            paciente_id = _normalizar_int(atendimento.id_paciente_spdata)
            pacientes_por_spdata_id.setdefault(
                paciente_id,
                _paciente_de_atendimento_spdata(atendimento),
            )

        agendas_paciente = db.session.execute(
            select(MedSpdataAgenda).where(
                MedSpdataAgenda.id_paciente_spdata.in_(pacientes_ids)
            )
        ).scalars().all()
        for agenda in agendas_paciente:
            paciente_id = _normalizar_int(agenda.id_paciente_spdata)
            pacientes_por_spdata_id.setdefault(
                paciente_id,
                _paciente_de_agenda_spdata(agenda),
            )

    pacientes_por_id_local = {}
    for atendimento in _set_por_ids(MedSpdataAtendimento, pacientes_ids):
        pacientes_por_id_local.setdefault(atendimento.id, _paciente_de_atendimento_spdata(atendimento))
    for agenda in _set_por_ids(MedSpdataAgenda, pacientes_ids):
        pacientes_por_id_local.setdefault(agenda.id, _paciente_de_agenda_spdata(agenda))

    documentos_por_id = {}
    if documentos_personalizados_ids:
        documentos = db.session.execute(
            select(DocumentoPersonalizado)
            .options(joinedload(DocumentoPersonalizado.atendimento))
            .where(DocumentoPersonalizado.id.in_(documentos_personalizados_ids))
        ).scalars().all()
        documentos_por_id = {
            documento.id: _paciente_de_atendimento_local(documento.atendimento)
            for documento in documentos
            if documento.atendimento
        }

    pacientes_por_evento = {}
    for evento in eventos:
        entidade_id = _normalizar_int(evento.entidade_id)
        paciente = None
        paciente_id = _paciente_id_direto_evento(evento)

        if evento.entidade in ENTIDADES_ATENDIMENTO_SPDATA:
            paciente = atendimentos_por_id.get(entidade_id)
        elif evento.entidade in ENTIDADES_AGENDA_SPDATA:
            paciente = agendas_por_id.get(entidade_id)
        elif evento.entidade == "documentos_medicos_personalizados":
            paciente = documentos_por_id.get(entidade_id)

        if paciente is None and paciente_id is not None:
            paciente = (
                pacientes_por_spdata_id.get(paciente_id)
                or pacientes_por_id_local.get(paciente_id)
                or _paciente_payload(paciente_id=paciente_id)
            )

        pacientes_por_evento[evento.id] = paciente

    return pacientes_por_evento


def _descricao_interacao_paciente(evento, paciente):
    if not paciente:
        return None

    acao = evento.acao.value if hasattr(evento.acao, "value") else str(evento.acao or "")
    if acao == "ALTEROU_STATUS_AGENDA":
        status = _status_descricao(evento.descricao)
        if status:
            return f"Médico atualizou o status do atendimento para {status}."
        return "Médico atualizou o status do atendimento do paciente."
    return DESCRICOES_INTERACAO_PACIENTE.get(acao)


def listar_auditorias(params):
    data_ini = parse_data(params.get("dataIni"))
    data_fim = parse_data(params.get("dataFim"))
    acao = (params.get("acao") or "").strip() or None
    entidade = (params.get("entidade") or "").strip() or None
    usuario_id = params.get("usuarioId", type=int)
    limit = min(max(params.get("limit", default=50, type=int) or 50, 1), 200)
    offset = max(params.get("offset", default=0, type=int) or 0, 0)

    filtros = []
    if data_ini:
        filtros.append(
            Auditoria.created_at >= _data_local_para_utc_sem_timezone(data_ini, time.min)
        )
    if data_fim:
        filtros.append(
            Auditoria.created_at < _data_local_para_utc_sem_timezone(
                data_fim + timedelta(days=1),
                time.min,
            )
        )
    if acao:
        filtros.append(Auditoria.acao == acao)
    if entidade:
        filtros.append(Auditoria.entidade == entidade)
    if usuario_id:
        filtros.append(Auditoria.usuario_id == usuario_id)

    query = (
        select(Auditoria)
        .options(joinedload(Auditoria.usuario))
        .where(*filtros)
        .order_by(Auditoria.created_at.desc())
        .limit(limit + 1)
        .offset(offset)
    )
    eventos = db.session.execute(query).scalars().all()
    has_more = len(eventos) > limit
    eventos_pagina = eventos[:limit]
    pacientes_por_evento = _mapear_pacientes_auditoria(eventos_pagina)

    items = []
    for evento in eventos_pagina:
        item = evento.to_dict()
        paciente = pacientes_por_evento.get(evento.id)
        item["paciente"] = paciente
        descricao_interacao = _descricao_interacao_paciente(evento, paciente)
        if descricao_interacao:
            item["descricao_direta"] = descricao_interacao
        items.append(item)

    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }


__all__ = ["listar_auditorias", "listar_retencao_exames", "parse_data", "registrar_auditoria"]
