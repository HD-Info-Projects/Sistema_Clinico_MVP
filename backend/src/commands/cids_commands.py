import click

from flask.cli import with_appcontext


@click.command("importar-cids-spdata")
@click.option(
    "--batch-size",
    default=200,
    type=click.IntRange(min=1),
    show_default=True,
    help="Quantidade de CIDs processados por lote.",
)
@with_appcontext
def importar_cids_spdata_command(batch_size):
    """Importa os CIDs da TBCID10 para o banco local."""

    from src.services.importar_cids_spdata import importar_cids_spdata

    click.echo("Iniciando importação dos CIDs do SPDATA...")

    try:
        resultado = importar_cids_spdata(batch_size=batch_size)
    except Exception as exc:
        raise click.ClickException(f"Falha ao importar CIDs: {exc}") from exc

    click.secho(
        (
            "\nImportação concluída:\n"
            f"  Lidos: {resultado['lidos']}\n"
            f"  Criados: {resultado['criados']}\n"
            f"  Atualizados: {resultado['atualizados']}\n"
            f"  Inalterados: {resultado['inalterados']}\n"
            f"  Duplicados: {resultado['duplicados']}\n"
            f"  Erros: {resultado['erros']}"
        ),
        fg="green",
    )
