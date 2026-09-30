import click

from flask.cli import with_appcontext


@click.command("importar-anamneses-spdata")
@click.option(
    "--batch-size",
    default=200,
    type=click.IntRange(min=1),
    show_default=True,
    help="Quantidade de evoluções processadas por lote.",
)
@click.option(
    "--desde",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Importa evoluções a partir desta data (AAAA-MM-DD).",
)
@click.option(
    "--completo",
    is_flag=True,
    default=False,
    help="Reimporta todas as evoluções (atualiza as existentes, sem duplicar).",
)
@with_appcontext
def importar_anamneses_spdata_command(batch_size, desde, completo):
    """Importa/espelha as anamneses (modelo MED26) do SPDATA para o banco local.

    Sem opções, continua a partir da última evolução já importada (com recuo
    de 2 dias para recapturar edições). Na primeira execução importa tudo.
    """

    if desde and completo:
        raise click.UsageError("Use --desde ou --completo, não os dois.")

    from src.services.importar_anamneses_spdata import importar_anamneses_spdata

    click.echo("Iniciando importação das anamneses do SPDATA...")

    try:
        resultado = importar_anamneses_spdata(
            batch_size=batch_size,
            desde=desde,
            completo=completo,
        )
    except Exception as exc:
        raise click.ClickException(f"Falha ao importar anamneses: {exc}") from exc

    inicio = resultado["desde"].strftime("%Y-%m-%d %H:%M") if resultado["desde"] else "todas"

    click.secho(
        (
            "\nImportação concluída:\n"
            f"  A partir de: {inicio}\n"
            f"  Lidos: {resultado['lidos']}\n"
            f"  Criados: {resultado['criados']}\n"
            f"  Atualizados: {resultado['atualizados']}\n"
            f"  Erros: {resultado['erros']}"
        ),
        fg="green",
    )
