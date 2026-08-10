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

    from src.services.importar_procedimentos_spdata import importar_procedimentos_spdata

    click.echo("Iniciando importação dos procedimentos do SPDATA...")

    resultado = importar_procedimentos_spdata(
        batch_size=batch_size,
    )

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
