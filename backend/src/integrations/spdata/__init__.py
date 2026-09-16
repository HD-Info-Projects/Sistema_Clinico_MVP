"""SPDATA Firebird integration facade.

This package exposes the existing SPDATA services through the integrations
namespace while the legacy service modules remain the source of behavior.
"""

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.services import medicos_spdata_service as medicos_service
from src.services import spdata_agenda_service as agenda_service
from src.services import spdata_atendimentos_service as atendimentos_service
from src.services import spdata_recepcao_service as recepcao_service
from src.services.exportar_logos_tiss import exportar_logos_tiss
from src.services.importar_convenios_spdata import importar_convenios_spdata
from src.services.importar_especialidades_spdata import importar_especialidades_spdata
from src.services.importar_procedimentos_spdata import importar_procedimentos_spdata
from src.services.medicos_spdata_service import (
    buscar_especialidades_medico_spdata,
    buscar_medicos_spdata,
    criar_usuario_medico_spdata,
    dados_medico_normalizados,
    upsert_usuario_medico_spdata,
)
from src.services.spdata_agenda_service import (
    buscar_agenda_spdata,
    sincronizar_agenda_spdata,
)
from src.services.spdata_atendimentos_service import (
    atualizar_status_agenda,
    buscar_atendimentos_spdata,
    get_crm_medico_usuario,
    listar_agenda_medica,
    listar_atendimentos_medsystem_para_frontend,
    listar_marcadores_agenda_medica,
    sincronizar_atendimentos_spdata,
)
from src.services.spdata_recepcao_service import (
    buscar_pacientes_spdata,
    listar_convenios_recepcao,
    listar_medicos_recepcao,
    listar_procedimentos_recepcao,
    salvar_atendimento_spdata,
    salvar_novo_atendimento_spdata,
    salvar_paciente_spdata,
)

__all__ = [
    "ConnectionDBFireBird",
    "agenda_service",
    "atendimentos_service",
    "atualizar_status_agenda",
    "buscar_agenda_spdata",
    "buscar_atendimentos_spdata",
    "buscar_especialidades_medico_spdata",
    "buscar_medicos_spdata",
    "buscar_pacientes_spdata",
    "criar_usuario_medico_spdata",
    "dados_medico_normalizados",
    "exportar_logos_tiss",
    "get_crm_medico_usuario",
    "importar_convenios_spdata",
    "importar_especialidades_spdata",
    "importar_procedimentos_spdata",
    "listar_agenda_medica",
    "listar_atendimentos_medsystem_para_frontend",
    "listar_convenios_recepcao",
    "listar_marcadores_agenda_medica",
    "listar_medicos_recepcao",
    "listar_procedimentos_recepcao",
    "medicos_service",
    "recepcao_service",
    "salvar_atendimento_spdata",
    "salvar_novo_atendimento_spdata",
    "salvar_paciente_spdata",
    "sincronizar_agenda_spdata",
    "sincronizar_atendimentos_spdata",
    "upsert_usuario_medico_spdata",
]
