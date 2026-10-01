from rq import get_current_job


def executar_spdata_sync_job(job_id):
    from src import create_app
    from src.integrations.spdata.catalog_sync import executar_job

    app = create_app()
    with app.app_context():
        rq_job = get_current_job()
        permitir_retry = bool(rq_job and (rq_job.retries_left or 0) > 0)
        return executar_job(
            job_id,
            permitir_retry=permitir_retry,
            expected_rq_job_id=rq_job.id if rq_job else None,
        )
