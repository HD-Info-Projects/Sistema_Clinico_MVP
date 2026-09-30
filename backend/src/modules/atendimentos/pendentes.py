"""Atendimentos que o médico deixou "em atendimento" sem finalizar.

Usado para perguntar ao médico, ao entrar em uma unidade, o que fazer com
atendimentos abertos de dias anteriores (retomar, finalizar ou cancelar) e
para impedir o logout com atendimento em andamento. Consulta apenas o MySQL
(sem sincronizar com o SPDATA), então é barato.
"""

from src.models.model_mydsystem.med_atendimentos_model import MedAtendimentos
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.modules.atendimentos.service import (
    agenda_para_frontend,
    buscar_convenios_locais,
    filtro_spdata_unidade,
    get_crm_medico_usuario,
    valores_status_medsystem,
)
from src.modules.unidades.service import resolver_unidade_usuario
from src.settings.extensions import db


def listar_atendimentos_pendentes(usuario_id, unidade_id=None, anteriores_a=None):
    """Lista atendimentos EM_ATENDIMENTO do médico na unidade ativa.

    Com `anteriores_a` (date), retorna só os de datas anteriores a ela.
    """
    unidade = resolver_unidade_usuario(usuario_id, unidade_id)
    crm_medico = get_crm_medico_usuario(usuario_id)

    filtros = [
        MedAtendimentos.status.in_(valores_status_medsystem("em-atendimento")),
        MedSpdataAtendimento.crm_medico == crm_medico,
        filtro_spdata_unidade(MedSpdataAtendimento, unidade),
    ]
    if anteriores_a is not None:
        filtros.append(MedAtendimentos.data_agenda < anteriores_a)

    registros = (
        db.session.query(MedSpdataAtendimento, MedAtendimentos)
        .join(
            MedAtendimentos,
            MedAtendimentos.med_spdata_atendimento_id == MedSpdataAtendimento.id,
        )
        .filter(*filtros)
        .order_by(
            MedAtendimentos.data_agenda.desc(),
            MedAtendimentos.hora_agenda.desc(),
            MedAtendimentos.id.desc(),
        )
        .all()
    )

    convenios_por_codigo = buscar_convenios_locais(
        spdata.id_convenio_spdata for spdata, _ in registros
    )
    return [
        agenda_para_frontend(spdata, atendimento, convenios_por_codigo)
        for spdata, atendimento in registros
    ]
