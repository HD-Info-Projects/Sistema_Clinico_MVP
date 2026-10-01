import logging
from datetime import UTC, datetime, timedelta

from flask import current_app
from redis.exceptions import RedisError
from rq import Retry
from rq.exceptions import InvalidJobOperation, NoSuchJobError
from rq.job import Job, JobStatus
from sqlalchemy.exc import IntegrityError

from src.jobs.queue import get_spdata_queue
from src.models.auditoria_model import AcaoAuditoria
from src.models.spdata_import_job_model import SpdataImportJob
from src.services.auditoria_service import registrar_auditoria
from src.settings.extensions import db


logger = logging.getLogger(__name__)

TARGETS = {"TODOS", "EXAMES", "PROCEDIMENTOS"}
ACTIVE_KEY = "spdata_catalog_import"


class InvalidTargetError(ValueError):
    pass


class ActiveJobError(RuntimeError):
    def __init__(self, job):
        self.job = job
        super().__init__("Já existe uma sincronização SPDATA em andamento.")


class QueueUnavailableError(RuntimeError):
    def __init__(self, job):
        self.job = job
        super().__init__("A fila de sincronização está indisponível.")


class InactiveJobError(RuntimeError):
    pass


def _agora():
    return datetime.now(UTC).replace(tzinfo=None)


def _normalizar_target(target):
    target = str(target or "TODOS").strip().upper()
    if target not in TARGETS:
        raise InvalidTargetError("Catálogo inválido. Use TODOS, EXAMES ou PROCEDIMENTOS.")
    return target


def buscar_job_ativo():
    return (
        SpdataImportJob.query
        .filter(SpdataImportJob.active_key == ACTIVE_KEY)
        .order_by(SpdataImportJob.id.desc())
        .first()
    )


def _reconciliar_job_expirado():
    job = buscar_job_ativo()
    if not job:
        return None

    timeout = current_app.config["SPDATA_JOB_TIMEOUT_SECONDS"]
    referencia = job.heartbeat_at or job.started_at or job.queued_at
    if referencia and referencia < _agora() - timedelta(seconds=timeout + 300):
        if job.rq_job_id:
            try:
                queue = get_spdata_queue()
                rq_job = Job.fetch(job.rq_job_id, connection=queue.connection)
                if rq_job.get_status(refresh=True) == JobStatus.STARTED:
                    return job
                try:
                    rq_job.cancel()
                except InvalidJobOperation:
                    pass
                rq_job.delete()
            except NoSuchJobError:
                pass
            except (RedisError, OSError):
                logger.exception("Falha ao cancelar job SPDATA expirado", extra={"job_id": job.id})
                raise QueueUnavailableError(job) from None

        job.status = "FAILED"
        job.active_key = None
        job.error_code = "JOB_EXPIRED"
        job.error_message = "A execução foi interrompida antes de ser concluída."
        job.finished_at = _agora()
        db.session.commit()
        return None

    return job


def criar_job(target, *, origin, requested_by_id=None, batch_size=None, max_attempts=2):
    target = _normalizar_target(target)
    ativo = _reconciliar_job_expirado()
    if ativo:
        raise ActiveJobError(ativo)

    job = SpdataImportJob(
        target=target,
        origin=origin,
        status="QUEUED",
        active_key=ACTIVE_KEY,
        requested_by_id=requested_by_id,
        batch_size=batch_size or current_app.config["SPDATA_IMPORT_BATCH_SIZE"],
        max_attempts=max_attempts,
        progress={},
        result={},
    )
    db.session.add(job)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        ativo = buscar_job_ativo()
        if ativo:
            raise ActiveJobError(ativo) from None
        raise
    return job


def enfileirar_job(job):
    from src.jobs.spdata_sync_job import executar_spdata_sync_job

    rq_job_id = f"spdata-import-{job.id}"
    job.rq_job_id = rq_job_id
    db.session.commit()
    try:
        queue = get_spdata_queue()
        queue.enqueue(
            executar_spdata_sync_job,
            job.id,
            job_id=rq_job_id,
            job_timeout=current_app.config["SPDATA_JOB_TIMEOUT_SECONDS"],
            retry=Retry(max=1, interval=[60]),
            result_ttl=current_app.config["SPDATA_JOB_RESULT_TTL_SECONDS"],
            failure_ttl=current_app.config["SPDATA_JOB_FAILURE_TTL_SECONDS"],
        )
        return job
    except (InvalidJobOperation, RedisError, OSError, RuntimeError):
        logger.exception("Falha ao enfileirar sincronização SPDATA", extra={"job_id": job.id})
        db.session.rollback()
        job = db.session.get(SpdataImportJob, job.id)
        job.status = "FAILED"
        job.active_key = None
        job.error_code = "QUEUE_UNAVAILABLE"
        job.error_message = "A fila de sincronização está indisponível."
        job.finished_at = _agora()
        db.session.commit()
        _auditar_resultado(
            job,
            AcaoAuditoria.FALHOU_SINCRONIZACAO_SPDATA,
            f"Falha ao enfileirar sincronização SPDATA; catálogo={job.target}",
        )
        raise QueueUnavailableError(job) from None


def criar_e_enfileirar_job(target, requested_by_id):
    job = criar_job(
        target,
        origin="ADMIN_API",
        requested_by_id=requested_by_id,
        max_attempts=2,
    )
    auditar_solicitacao(job, requested_by_id)
    return enfileirar_job(job)


def auditar_solicitacao(job, usuario_id):
    registrar_auditoria(
        AcaoAuditoria.SOLICITOU_SINCRONIZACAO_SPDATA,
        entidade="spdata_import_job",
        entidade_id=job.id,
        usuario_id=usuario_id,
        descricao=f"Solicitou sincronização SPDATA; catálogo={job.target}",
    )


def criar_job_cli(target, batch_size):
    return criar_job(
        target,
        origin="CLI",
        batch_size=batch_size,
        max_attempts=1,
    )


def _atualizar_progresso(job_id, stage, contadores):
    job = db.session.get(SpdataImportJob, job_id)
    progresso = dict(job.progress or {})
    progresso[stage.lower()] = dict(contadores)
    job.progress = progresso
    job.heartbeat_at = _agora()
    db.session.commit()


def _stages(target):
    if target == "EXAMES":
        return ("EXAMES",)
    if target == "PROCEDIMENTOS":
        return ("PROCEDIMENTOS",)
    return ("EXAMES", "PROCEDIMENTOS")


def _executar_stage(job, stage):
    callback = lambda contadores: _atualizar_progresso(job.id, stage, contadores)
    if stage == "EXAMES":
        from src.services.importar_exames_spdata import importar_exames_spdata
        return importar_exames_spdata(batch_size=job.batch_size, on_progress=callback)

    from src.services.importar_procedimentos_spdata import importar_procedimentos_spdata
    return importar_procedimentos_spdata(batch_size=job.batch_size, on_progress=callback)


def _auditar_resultado(job, acao, descricao):
    registrar_auditoria(
        acao,
        entidade="spdata_import_job",
        entidade_id=job.id,
        usuario_id=job.requested_by_id,
        descricao=descricao,
    )


def executar_job(job_id, *, permitir_retry=False, expected_rq_job_id=None):
    query = SpdataImportJob.query.filter(
        SpdataImportJob.id == job_id,
        SpdataImportJob.active_key == ACTIVE_KEY,
        SpdataImportJob.status.in_({"QUEUED", "RETRYING"}),
    )
    if expected_rq_job_id:
        query = query.filter(SpdataImportJob.rq_job_id == expected_rq_job_id)

    acquired = query.update(
        {
            SpdataImportJob.status: "RUNNING",
            SpdataImportJob.attempts: SpdataImportJob.attempts + 1,
            SpdataImportJob.heartbeat_at: _agora(),
        },
        synchronize_session=False,
    )
    db.session.commit()
    if not acquired:
        raise InactiveJobError(f"Job SPDATA {job_id} não está disponível para execução")

    job = db.session.get(SpdataImportJob, job_id)
    job.started_at = job.started_at or _agora()
    job.error_code = None
    job.error_message = None
    db.session.commit()

    try:
        resultados = dict(job.result or {})
        for stage in _stages(job.target):
            stage_key = stage.lower()
            if resultados.get(stage_key, {}).get("completed"):
                continue

            job.current_stage = stage
            progresso = dict(job.progress or {})
            progresso[stage_key] = {
                "lidos": 0,
                "criados": 0,
                "atualizados": 0,
                "erros": 0,
            }
            job.progress = progresso
            job.heartbeat_at = _agora()
            db.session.commit()

            contadores = _executar_stage(job, stage)
            resultados[stage_key] = {**contadores, "completed": True}
            job = db.session.get(SpdataImportJob, job_id)
            job.result = dict(resultados)
            job.heartbeat_at = _agora()
            db.session.commit()

        total_erros = sum(item.get("erros", 0) for item in resultados.values())
        job.status = "SUCCEEDED_WITH_ERRORS" if total_erros else "SUCCEEDED"
        job.current_stage = None
        job.active_key = None
        job.finished_at = _agora()
        job.heartbeat_at = _agora()
        db.session.commit()
        _auditar_resultado(
            job,
            AcaoAuditoria.SINCRONIZOU_SPDATA,
            f"Sincronização SPDATA concluída; catálogo={job.target}; erros={total_erros}",
        )
        return job.to_dict()
    except Exception as error:
        logger.exception("Falha na sincronização SPDATA", extra={"job_id": job_id})
        db.session.rollback()
        job = db.session.get(SpdataImportJob, job_id)
        job.status = "RETRYING" if permitir_retry else "FAILED"
        job.error_code = error.__class__.__name__[:100]
        job.error_message = "Falha ao acessar ou processar os dados do SPDATA."
        job.heartbeat_at = _agora()
        if not permitir_retry:
            job.active_key = None
            job.current_stage = None
            job.finished_at = _agora()
        db.session.commit()
        if not permitir_retry:
            _auditar_resultado(
                job,
                AcaoAuditoria.FALHOU_SINCRONIZACAO_SPDATA,
                f"Sincronização SPDATA falhou; catálogo={job.target}; código={job.error_code}",
            )
        raise


def listar_jobs(limit=20, offset=0):
    query = SpdataImportJob.query.order_by(
        SpdataImportJob.created_at.desc(),
        SpdataImportJob.id.desc(),
    )
    jobs = query.offset(offset).limit(limit + 1).all()
    active_job = buscar_job_ativo()
    return {
        "items": [job.to_dict() for job in jobs[:limit]],
        "limit": limit,
        "offset": offset,
        "has_more": len(jobs) > limit,
        "active_job": active_job.to_dict() if active_job else None,
    }


def buscar_job(job_id):
    return db.session.get(SpdataImportJob, job_id)
