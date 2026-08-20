import json
import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy import and_, delete, exists, func, select, text

from src.models.atendimentos_model import Atendimento
from src.models.auditoria_model import AcaoAuditoria, Auditoria
from src.models.fila_sincronizacao_model import (
    FilaSincronizacao,
    StatusSincronizacao,
)
from src.models.log_integracao_model import LogIntegracao
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.models.model_mydsystem.med_spdata_atendimentos_model import (
    MedSpdataAtendimento,
)
# Carrega no metadata a FK que protege atendimentos SPDATA vinculados.
from src.models.model_mydsystem.med_atendimentos_model import MedAtendimentos  # noqa: F401
from src.settings.extensions import db


TABELAS_CLINICAS_PROTEGIDAS = frozenset({
    "atendimentos",
    "anamneses",
    "evolucoes_medicas",
    "evolucoes_medicas_versoes",
    "diagnosticos",
    "prescricoes",
    "solicitacoes_exames",
    "documentos_medicos",
})

CONFIG_DEFAULTS = {
    "LGPD_RETENTION_LOGS_INTEGRACAO_DAYS": 180,
    "LGPD_RETENTION_FILA_SINCRONIZACAO_DAYS": 90,
    "LGPD_RETENTION_AUDITORIA_DAYS": 1825,
    "LGPD_RETENTION_SPDATA_ESPELHO_DAYS": 730,
    "LGPD_RETENTION_BATCH_SIZE": 500,
}


@dataclass(frozen=True)
class RegraRetencao:
    nome: str
    modelo: type
    campo_data: object
    config_dias: str
    filtros: tuple = ()
    protecoes: tuple = ()
    somente_data: bool = False
    excluir_automaticamente: bool = True


REGRAS_RETENCAO = (
    RegraRetencao(
        "logs_integracao",
        LogIntegracao,
        LogIntegracao.created_at,
        "LGPD_RETENTION_LOGS_INTEGRACAO_DAYS",
    ),
    RegraRetencao(
        "fila_sincronizacao",
        FilaSincronizacao,
        FilaSincronizacao.updated_at,
        "LGPD_RETENTION_FILA_SINCRONIZACAO_DAYS",
        filtros=(
            FilaSincronizacao.status.in_((
                StatusSincronizacao.SINCRONIZADO,
                StatusSincronizacao.CANCELADO,
            )),
        ),
    ),
    RegraRetencao(
        "auditorias",
        Auditoria,
        Auditoria.created_at,
        "LGPD_RETENTION_AUDITORIA_DAYS",
    ),
    RegraRetencao(
        "MED_SPDATA_AGENDA",
        MedSpdataAgenda,
        MedSpdataAgenda.data_agenda,
        "LGPD_RETENTION_SPDATA_ESPELHO_DAYS",
        protecoes=(
            ~exists(
                select(1).select_from(Atendimento).where(
                    Atendimento.spdata_agenda_id == MedSpdataAgenda.spdata_agenda_id
                )
            ),
        ),
        somente_data=True,
        excluir_automaticamente=False,
    ),
    RegraRetencao(
        "MED_SPDATA_ATENDIMENTOS",
        MedSpdataAtendimento,
        MedSpdataAtendimento.data_atendimento,
        "LGPD_RETENTION_SPDATA_ESPELHO_DAYS",
        protecoes=(
            ~exists(
                select(1).select_from(Atendimento).where(
                    Atendimento.spdata_atendimento_id
                    == MedSpdataAtendimento.spdata_atendimento_id
                )
            ),
            ~exists(
                select(1).select_from(MedAtendimentos).where(
                    MedAtendimentos.spdata_atendimento_id
                    == MedSpdataAtendimento.spdata_atendimento_id
                )
            ),
        ),
        somente_data=True,
        excluir_automaticamente=False,
    ),
)


def _valor_config(config, chave):
    valor = int(config.get(chave, CONFIG_DEFAULTS[chave]))
    if valor <= 0:
        raise ValueError(f"{chave} deve ser maior que zero")
    return valor


def _agora_utc_sem_timezone(agora):
    agora = agora or datetime.now(timezone.utc)
    if agora.tzinfo is not None:
        return agora.astimezone(timezone.utc).replace(tzinfo=None)
    return agora


def _filtros_fk(modelo):
    """Preserva registros referenciados por qualquer FK conhecida no metadata."""
    tabela_alvo = modelo.__table__
    filtros = []

    for tabela_origem in db.metadata.tables.values():
        for constraint in tabela_origem.foreign_key_constraints:
            elementos = tuple(constraint.elements)
            if not elementos or not all(
                elemento.column.table is tabela_alvo for elemento in elementos
            ):
                continue

            vinculo = and_(*(
                elemento.parent == elemento.column for elemento in elementos
            ))
            filtros.append(~exists(select(1).select_from(tabela_origem).where(vinculo)))

    return tuple(filtros)


def _filtros_regra(regra, corte, *, proteger_fks):
    filtros = (regra.campo_data < corte, *regra.filtros)
    if proteger_fks:
        filtros += (*regra.protecoes, *_filtros_fk(regra.modelo))
    return filtros


def _contar(session, regra, corte, *, proteger_fks):
    statement = select(func.count()).select_from(regra.modelo).where(
        *_filtros_regra(regra, corte, proteger_fks=proteger_fks)
    )
    return session.execute(statement).scalar_one()


def _ids_elegiveis(session, regra, corte):
    chave_primaria = regra.modelo.__mapper__.primary_key
    if len(chave_primaria) != 1:
        raise RuntimeError(f"A tabela {regra.nome} nao possui chave primaria simples")

    return tuple(session.execute(
        select(chave_primaria[0])
        .where(*_filtros_regra(regra, corte, proteger_fks=True))
        .order_by(chave_primaria[0])
    ).scalars())


def _hash_ids(ids):
    digest = hashlib.sha256()
    for identificador in ids:
        digest.update(str(identificador).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _excluir_em_lotes(session, regra, corte, ids_aprovados, batch_size):
    chave_primaria = regra.modelo.__mapper__.primary_key
    if len(chave_primaria) != 1:
        raise RuntimeError(f"A tabela {regra.nome} nao possui chave primaria simples")

    chave_primaria = chave_primaria[0]
    filtros = _filtros_regra(regra, corte, proteger_fks=True)
    excluidos = 0

    for inicio in range(0, len(ids_aprovados), batch_size):
        ids = ids_aprovados[inicio:inicio + batch_size]
        resultado = session.execute(
            delete(regra.modelo)
            .where(chave_primaria.in_(ids), *filtros)
            .execution_options(synchronize_session=False)
        )
        if resultado.rowcount != len(ids):
            raise RuntimeError(
                f"A tabela {regra.nome} mudou durante a exclusao; operacao revertida"
            )
        excluidos += resultado.rowcount

    return excluidos


def _gerar_hash_plano(resultado):
    plano = {
        "executado_em": resultado["executado_em"],
        "batch_size": resultado["batch_size"],
        "tabelas": {
            nome: {
                "campo_data": dados["campo_data"],
                "retencao_dias": dados["retencao_dias"],
                "corte": dados["corte"],
                "candidatos": dados["candidatos"],
                "protegidos_por_vinculo": dados["protegidos_por_vinculo"],
                "elegiveis": dados["elegiveis"],
                "hash_ids_elegiveis": dados["hash_ids_elegiveis"],
                "exclusao_automatica": dados["exclusao_automatica"],
            }
            for nome, dados in resultado["tabelas"].items()
        },
    }
    payload = json.dumps(
        plano,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _descricao_auditoria(resultado, contexto_execucao):
    resumo = {
        "batch_size": resultado["batch_size"],
        "plan_hash": resultado["plan_hash"],
        "backup_reference": contexto_execucao["backup_reference"],
        "approval_reference": contexto_execucao["approval_reference"],
        "operator": contexto_execucao["operator"],
        "legal_hold_checked": True,
        "total_excluidos": resultado["total_excluidos"],
        "tabelas": {
            nome: {
                "corte": dados["corte"],
                "candidatos": dados["candidatos"],
                "protegidos_por_vinculo": dados["protegidos_por_vinculo"],
                "elegiveis": dados["elegiveis"],
                "excluidos": dados["excluidos"],
            }
            for nome, dados in resultado["tabelas"].items()
        },
    }
    return json.dumps(resumo, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _processar(
    session,
    config,
    agora,
    batch_size,
    *,
    dry_run,
    expected_plan_hash=None,
):
    resultado = {
        "modo": "dry-run" if dry_run else "execute",
        "executado_em": agora.isoformat(),
        "batch_size": batch_size,
        "tabelas": {},
        "total_elegiveis": 0,
        "total_protegidos_por_vinculo": 0,
        "total_bloqueadores": 0,
        "total_excluidos": 0,
    }
    cortes = {}
    ids_por_regra = {}

    for regra in REGRAS_RETENCAO:
        dias = _valor_config(config, regra.config_dias)
        corte_datetime = agora - timedelta(days=dias)
        corte = corte_datetime.date() if regra.somente_data else corte_datetime
        candidatos = _contar(session, regra, corte, proteger_fks=False)
        ids_elegiveis = _ids_elegiveis(session, regra, corte)
        elegiveis = len(ids_elegiveis)
        hash_ids_elegiveis = _hash_ids(ids_elegiveis)
        ids_por_regra[regra.nome] = ids_elegiveis
        cortes[regra.nome] = corte

        resultado["tabelas"][regra.nome] = {
            "campo_data": regra.campo_data.key,
            "retencao_dias": dias,
            "corte": corte.isoformat(),
            "candidatos": candidatos,
            "protegidos_por_vinculo": candidatos - elegiveis,
            "elegiveis": elegiveis,
            "hash_ids_elegiveis": hash_ids_elegiveis,
            "exclusao_automatica": regra.excluir_automaticamente,
            "excluidos": 0,
        }
        resultado["total_elegiveis"] += elegiveis
        resultado["total_protegidos_por_vinculo"] += candidatos - elegiveis
        if regra.excluir_automaticamente:
            resultado["total_bloqueadores"] += candidatos - elegiveis

    if dry_run:
        resultado["plan_hash"] = _gerar_hash_plano(resultado)
        return resultado

    if resultado["total_bloqueadores"]:
        tabelas = ", ".join(
            nome
            for nome, dados in resultado["tabelas"].items()
            if dados["exclusao_automatica"] and dados["protegidos_por_vinculo"]
        )
        raise RuntimeError(
            "Descarte abortado: existem registros antigos protegidos por vinculos "
            f"nas tabelas {tabelas}. Revise o dry-run sem remover dados clinicos."
        )

    resultado["plan_hash"] = _gerar_hash_plano(resultado)
    if expected_plan_hash and resultado["plan_hash"] != expected_plan_hash.lower():
        raise RuntimeError(
            "O estado atual diverge do dry-run aprovado; gere e revise um novo plano"
        )
    for regra in REGRAS_RETENCAO:
        if not regra.excluir_automaticamente:
            continue
        excluidos = _excluir_em_lotes(
            session,
            regra,
            cortes[regra.nome],
            ids_por_regra[regra.nome],
            batch_size,
        )
        resultado["tabelas"][regra.nome]["excluidos"] = excluidos
        resultado["total_excluidos"] += excluidos

    return resultado


@contextmanager
def _lock_execucao(session):
    """Impede duas execucoes simultaneas no MySQL."""
    bind = session.get_bind()
    if bind.dialect.name != "mysql":
        yield
        return

    nome_lock = "sistema_clinico:lgpd_retencao"
    with bind.connect() as connection:
        adquirido = connection.execute(
            text("SELECT GET_LOCK(:nome, 0)"),
            {"nome": nome_lock},
        ).scalar_one()
        if adquirido != 1:
            raise RuntimeError("Ja existe uma execucao da retencao LGPD em andamento")
        try:
            yield
        finally:
            connection.execute(
                text("SELECT RELEASE_LOCK(:nome)"),
                {"nome": nome_lock},
            )


def _validar_contexto_execucao(plan_hash, contexto_execucao):
    if not isinstance(plan_hash, str) or len(plan_hash) != 64:
        raise ValueError("Informe o hash SHA-256 do plano gerado pelo dry-run")
    try:
        int(plan_hash, 16)
    except ValueError as exc:
        raise ValueError("O hash do plano deve ser um SHA-256 hexadecimal") from exc

    if not contexto_execucao or not contexto_execucao.get("legal_hold_checked"):
        raise ValueError("Confirme a verificacao de preservacao legal")
    for chave in ("backup_reference", "approval_reference", "operator"):
        valor = str(contexto_execucao.get(chave) or "").strip()
        if not valor or len(valor) > 200:
            raise ValueError(f"Informe {chave} com ate 200 caracteres")
        contexto_execucao[chave] = valor


def executar_retencao_lgpd(
    *,
    dry_run,
    agora=None,
    session=None,
    config=None,
    plan_hash=None,
    contexto_execucao=None,
):
    """Simula ou executa a politica LGPD sobre uma lista fechada de tabelas."""
    session = db.session if session is None else session
    if not hasattr(session, "in_transaction") and callable(session):
        session = session()
    config = current_app.config if config is None else config
    agora = _agora_utc_sem_timezone(agora)
    batch_size = _valor_config(config, "LGPD_RETENTION_BATCH_SIZE")

    tabelas_alvo = {regra.modelo.__tablename__ for regra in REGRAS_RETENCAO}
    if tabelas_alvo & TABELAS_CLINICAS_PROTEGIDAS:
        raise RuntimeError("Uma tabela clinica foi incluida na politica de descarte")

    if dry_run:
        tinha_transacao = session.in_transaction()
        try:
            with session.no_autoflush:
                return _processar(
                    session,
                    config,
                    agora,
                    batch_size,
                    dry_run=True,
                )
        finally:
            if not tinha_transacao and session.in_transaction():
                session.rollback()

    contexto_execucao = dict(contexto_execucao or {})
    _validar_contexto_execucao(plan_hash, contexto_execucao)

    try:
        with _lock_execucao(session):
            with session.begin():
                resultado = _processar(
                    session,
                    config,
                    agora,
                    batch_size,
                    dry_run=False,
                    expected_plan_hash=plan_hash,
                )
                session.add(Auditoria(
                    acao=AcaoAuditoria.RETENCAO_DESCARTE_EXECUTADA.value,
                    entidade="politica_lgpd_retencao",
                    descricao=_descricao_auditoria(resultado, contexto_execucao),
                    created_at=agora,
                ))
        return resultado
    except Exception:
        session.rollback()
        raise
