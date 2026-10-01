from sqlalchemy import and_, or_, select

from src.models.model_mydsystem.med_atendimento_prioridade_model import (
    MedAtendimentoPrioridade,
)
from src.settings.extensions import db


ORIGEM_AGENDA = "agenda"
ORIGEM_ATENDIMENTO = "atendimento"
ORIGENS_PRIORIDADE = {ORIGEM_AGENDA, ORIGEM_ATENDIMENTO}


def validar_referencia_prioridade(origem, spdata_id):
    if origem not in ORIGENS_PRIORIDADE:
        raise ValueError("prioridadeOrigem inválida")
    if isinstance(spdata_id, bool) or not isinstance(spdata_id, int) or spdata_id <= 0:
        raise ValueError("prioridadeSpdataId deve ser um inteiro positivo")
    return origem, spdata_id


def referencia_prioridade(id_agendamento, id_atendimento):
    if id_agendamento is not None:
        return ORIGEM_AGENDA, int(id_agendamento)
    return (
        ORIGEM_ATENDIMENTO,
        int(id_atendimento) if id_atendimento is not None else None,
    )


def buscar_prioridades_locais(unidade_id, referencias):
    ids_por_origem = {origem: set() for origem in ORIGENS_PRIORIDADE}
    for origem, spdata_id in referencias:
        if origem in ids_por_origem and spdata_id is not None:
            ids_por_origem[origem].add(int(spdata_id))

    filtros = [
        and_(
            MedAtendimentoPrioridade.origem == origem,
            MedAtendimentoPrioridade.spdata_id.in_(ids),
        )
        for origem, ids in ids_por_origem.items()
        if ids
    ]
    if not filtros:
        return {}

    registros = db.session.execute(
        select(MedAtendimentoPrioridade).where(
            MedAtendimentoPrioridade.unidade_id == unidade_id,
            or_(*filtros),
        )
    ).scalars().all()
    return {
        (registro.origem, registro.spdata_id): bool(registro.prioridade)
        for registro in registros
    }


def definir_prioridade_local(unidade_id, origem, spdata_id, prioridade):
    origem, spdata_id = validar_referencia_prioridade(origem, spdata_id)
    if not isinstance(prioridade, bool):
        raise ValueError("prioridade deve ser boolean")

    registro = db.session.execute(
        select(MedAtendimentoPrioridade).where(
            MedAtendimentoPrioridade.unidade_id == unidade_id,
            MedAtendimentoPrioridade.origem == origem,
            MedAtendimentoPrioridade.spdata_id == spdata_id,
        )
    ).scalars().first()
    if registro is None:
        registro = MedAtendimentoPrioridade(
            unidade_id=unidade_id,
            origem=origem,
            spdata_id=spdata_id,
            prioridade=prioridade,
        )
        db.session.add(registro)
    else:
        registro.prioridade = prioridade

    db.session.commit()
    return registro
