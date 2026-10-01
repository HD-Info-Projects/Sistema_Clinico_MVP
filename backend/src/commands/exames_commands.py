import click
from flask.cli import with_appcontext


@click.command("importar-exames-spdata")
@click.option(
    "--batch-size",
    default=200,
    type=click.IntRange(min=1),
    show_default=True,
    help="Quantidade de exames processados por lote.",
)
@with_appcontext
def importar_exames_spdata_command(batch_size):
    """Importa os exames da SITABPRO para o banco local."""

    from src.integrations.spdata.catalog_sync import (
        ActiveJobError,
        criar_job_cli,
        executar_job,
    )

    click.echo("Iniciando importação dos exames do SPDATA...")

    try:
        job = criar_job_cli("EXAMES", batch_size)
        executar_job(job.id)
    except ActiveJobError as error:
        raise click.ClickException(
            f"Já existe uma sincronização em andamento (job {error.job.id})."
        ) from None

    resultado = job.result["exames"]

    click.secho(
        (
            "\nImportação concluída:\n"
            f"  Lidos: {resultado['lidos']}\n"
            f"  Criados: {resultado['criados']}\n"
            f"  Atualizados: {resultado['atualizados']}\n"
            f"  Erros: {resultado['erros']}"
        ),
        fg="green",
    )
