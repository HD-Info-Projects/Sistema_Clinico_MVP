import click
from flask.cli import with_appcontext


@click.command("importar-procedimentos-spdata")
@click.option(
    "--batch-size",
    default=200,
    type=click.IntRange(min=1),
    show_default=True,
    help="Quantidade de procedimentos processados por lote.",
)
@with_appcontext
def importar_procedimentos_spdata_command(batch_size):
    """Importa os procedimentos da tabela 98 do SPDATA para o banco local."""

    from src.integrations.spdata.catalog_sync import (
        ActiveJobError,
        criar_job_cli,
        executar_job,
    )

    click.echo("Iniciando importação dos procedimentos do SPDATA...")

    try:
        job = criar_job_cli("PROCEDIMENTOS", batch_size)
        executar_job(job.id)
    except ActiveJobError as error:
        raise click.ClickException(
            f"Já existe uma sincronização em andamento (job {error.job.id})."
        ) from None

    resultado = job.result["procedimentos"]

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
