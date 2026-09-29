"""Encerramento manual (comando de admin) de atendimentos que ficaram "em atendimento".

O fluxo normal é o médico decidir, ao entrar na unidade, o que fazer com
atendimentos esquecidos (modal de atendimento pendente no frontend). Este
serviço é uma ferramenta de limpeza: marca como ATENDIDO, sem conteúdo clínico
(o rascunho vive apenas no navegador do médico), atendimentos de dias
anteriores, e registra auditoria. Nunca toca atendimentos de hoje.

Pacientes "em espera" (check-in sem atendimento) NÃO são alterados: eles não
foram atendidos e são tratados pelo relatório de no-show da recepção.
"""

from datetime import date

from flask import current_app
from sqlalchemy import select

from src.models.auditoria_model import AcaoAuditoria
from src.models.model_mydsystem.med_atendimentos_model import (
    MedAtendimentos,
    StatusAtendimentoMedSystem,
)
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.models.unidade_model import Unidade
from src.modules.atendimentos.service import marcar_preventivos_atendidos
from src.modules.lgpd.service import registrar_auditoria
from src.settings.extensions import db
from src.shared.response_cache import apagar_cache_por_padrao


def buscar_atendimentos_pendentes(hoje=None, unidade_id=None, crm_medico=None):
    # Só dias anteriores: um atendimento de hoje pode estar em andamento.
    hoje = hoje or date.today()
    query = select(MedAtendimentos).where(
        MedAtendimentos.status == StatusAtendimentoMedSystem.EM_ATENDIMENTO.value,
        MedAtendimentos.data_agenda < hoje,
    )
    if unidade_id is not None:
        query = query.where(MedAtendimentos.unidade_id == unidade_id)
    if crm_medico:
        query = query.join(
            MedSpdataAtendimento,
            MedSpdataAtendimento.id == MedAtendimentos.med_spdata_atendimento_id,
        ).where(MedSpdataAtendimento.crm_medico == crm_medico)

    return db.session.execute(
        query.order_by(MedAtendimentos.data_agenda, MedAtendimentos.id)
    ).scalars().all()


def _resumo(atendimento):
    return {
        "id": atendimento.id,
        "data": atendimento.data_agenda.isoformat() if atendimento.data_agenda else None,
        "hora": atendimento.hora_agenda.strftime("%H:%M") if atendimento.hora_agenda else None,
        "medico": atendimento.medico,
        "unidade_id": atendimento.unidade_id,
    }


def _marcar_preventivos(atendimento):
    spdata = db.session.get(MedSpdataAtendimento, atendimento.med_spdata_atendimento_id)
    unidade = db.session.get(Unidade, atendimento.unidade_id) if atendimento.unidade_id else None
    if spdata is None or unidade is None:
        return
    marcar_preventivos_atendidos(spdata, unidade)


def encerrar_atendimentos_pendentes(
    *,
    hoje=None,
    unidade_id=None,
    crm_medico=None,
    dry_run=False,
    origem="comando",
):
    """Encerra atendimentos EM_ATENDIMENTO antigos. Retorna um resumo.

    Cada atendimento é processado e commitado individualmente: uma falha em um
    registro não impede o encerramento dos demais.
    """
    pendentes = buscar_atendimentos_pendentes(
        hoje=hoje,
        unidade_id=unidade_id,
        crm_medico=crm_medico,
    )
    resultado = {
        "dry_run": dry_run,
        "encontrados": len(pendentes),
        "encerrados": [],
        "falhas": [],
    }
    if dry_run or not pendentes:
        resultado["encerrados"] = [_resumo(a) for a in pendentes] if dry_run else []
        return resultado

    for atendimento in pendentes:
        resumo = _resumo(atendimento)
        try:
            atendimento.marcar_atendido()
            _marcar_preventivos(atendimento)
            registrar_auditoria(
                AcaoAuditoria.ENCERROU_ATENDIMENTO_AUTOMATICAMENTE,
                entidade="agenda_medica",
                entidade_id=atendimento.med_spdata_atendimento_id,
                usuario_id=None,
                descricao=(
                    "Atendimento encerrado automaticamente por não ter sido finalizado. "
                    f"origem={origem} data={resumo['data']} medico={resumo['medico'] or ''}"
                ),
                commit=False,
            )
            db.session.commit()
            resultado["encerrados"].append(resumo)
        except Exception as exc:  # noqa: BLE001 - segue para os próximos
            db.session.rollback()
            current_app.logger.exception("Falha ao encerrar atendimento pendente id=%s", resumo["id"])
            resultado["falhas"].append({**resumo, "erro": exc.__class__.__name__})

    if resultado["encerrados"]:
        for padrao in ("perf:agenda_medica:*", "perf:check_in:*", "perf:no_show:*"):
            apagar_cache_por_padrao(padrao)

    return resultado
