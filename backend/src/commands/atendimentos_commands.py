import click
from flask import current_app
from flask.cli import with_appcontext

from src.modules.atendimentos.encerramento import encerrar_atendimentos_pendentes


@click.command("encerrar-atendimentos-pendentes")
@click.option("--dry-run", is_flag=True, help="Lista o que seria encerrado sem alterar o banco.")
@click.option("--unidade-id", type=int, default=None, help="Restringe a uma unidade.")
@with_appcontext
def encerrar_atendimentos_pendentes_command(dry_run, unidade_id):
    """Encerra atendimentos de dias anteriores que ficaram 'em atendimento'."""
    try:
        resultado = encerrar_atendimentos_pendentes(
            unidade_id=unidade_id,
            dry_run=dry_run,
            origem="comando",
        )
    except Exception as exc:
        current_app.logger.exception("Falha ao encerrar atendimentos pendentes")
        raise click.ClickException(f"Falha ao encerrar atendimentos pendentes: {exc}") from exc

    titulo = "Simulação (nada foi alterado)" if dry_run else "Encerramento concluído"
    click.secho(titulo, fg="yellow" if dry_run else "green", bold=True)
    click.echo(f"Encontrados: {resultado['encontrados']}")

    rotulo = "Seriam encerrados" if dry_run else "Encerrados"
    click.echo(f"{rotulo}: {len(resultado['encerrados'])}")
    for item in resultado["encerrados"]:
        click.echo(
            f"  - id={item['id']} data={item['data']} hora={item['hora'] or '-'} "
            f"unidade={item['unidade_id']} medico={item['medico'] or '-'}"
        )

    if resultado["falhas"]:
        click.secho(f"Falhas: {len(resultado['falhas'])}", fg="red", bold=True)
        for item in resultado["falhas"]:
            click.echo(f"  - id={item['id']} data={item['data']} erro={item['erro']}")
        raise click.ClickException("Alguns atendimentos não puderam ser encerrados.")
