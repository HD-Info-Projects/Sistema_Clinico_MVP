from datetime import UTC, datetime, timedelta

import click
from flask import current_app
from flask.cli import with_appcontext

from src.services.lgpd_retencao_service import executar_retencao_lgpd


PLAN_MAX_AGE = timedelta(hours=24)


def _parse_plan_reference(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise click.UsageError(
            "--plan-reference deve usar o ISO exibido em 'Referencia UTC'."
        ) from exc
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)

    now = datetime.now(UTC).replace(tzinfo=None)
    if parsed > now + timedelta(minutes=5) or now - parsed > PLAN_MAX_AGE:
        raise click.UsageError("O plano deve ter sido gerado nas ultimas 24 horas.")
    return parsed


@click.command("lgpd-retencao")
@click.option("--dry-run", is_flag=True, help="Simula o descarte sem alterar o banco.")
@click.option("--execute", is_flag=True, help="Executa o descarte e registra auditoria.")
@click.option("--plan-hash", help="Hash SHA-256 exibido pelo dry-run aprovado.")
@click.option("--plan-reference", help="Referencia UTC exibida pelo dry-run aprovado.")
@click.option("--backup-reference", help="Identificador do backup valido do ciclo.")
@click.option("--approval-reference", help="Chamado ou aprovacao formal do descarte.")
@click.option("--operator", help="Conta tecnica ou operador responsavel pela execucao.")
@click.option(
    "--confirm-no-legal-hold",
    is_flag=True,
    help="Confirma que preservacoes legais e incidentes foram verificados.",
)
@with_appcontext
def lgpd_retencao_command(
    dry_run,
    execute,
    plan_hash,
    plan_reference,
    backup_reference,
    approval_reference,
    operator,
    confirm_no_legal_hold,
):
    """Aplica os prazos LGPD de retencao e descarte."""
    if dry_run == execute:
        raise click.UsageError("Informe exatamente uma opcao: --dry-run ou --execute.")
    if dry_run and any((
        plan_hash,
        plan_reference,
        backup_reference,
        approval_reference,
        operator,
        confirm_no_legal_hold,
    )):
        raise click.UsageError("Opcoes de aprovacao sao aceitas somente com --execute.")
    if execute and not all((
        plan_hash,
        plan_reference,
        backup_reference,
        approval_reference,
        operator,
        confirm_no_legal_hold,
    )):
        raise click.UsageError(
            "--execute exige --plan-hash, --plan-reference, --backup-reference, "
            "--approval-reference, "
            "--operator "
            "e --confirm-no-legal-hold."
        )

    reference_time = _parse_plan_reference(plan_reference) if execute else None
    try:
        resultado = executar_retencao_lgpd(
            dry_run=dry_run,
            agora=reference_time,
            plan_hash=plan_hash,
            contexto_execucao={
                "backup_reference": backup_reference,
                "approval_reference": approval_reference,
                "operator": operator,
                "legal_hold_checked": confirm_no_legal_hold,
            } if execute else None,
        )
    except Exception as exc:
        current_app.logger.exception("Falha na politica LGPD de retencao e descarte")
        raise click.ClickException(
            "Falha ao processar a retencao; nenhuma alteracao desta execucao foi confirmada."
        ) from exc

    click.echo(f"Modo: {resultado['modo']}")
    click.echo(f"Referencia UTC: {resultado['executado_em']}")
    click.echo(f"Hash do plano: {resultado['plan_hash']}")
    for nome, dados in resultado["tabelas"].items():
        click.echo(
            f"{nome}: corte={dados['corte']} campo={dados['campo_data']} "
            f"elegiveis={dados['elegiveis']} "
            f"protegidos_por_vinculo={dados['protegidos_por_vinculo']} "
            f"exclusao_automatica={str(dados['exclusao_automatica']).lower()} "
            f"excluidos={dados['excluidos']}"
        )

    click.secho(
        f"Total excluido: {resultado['total_excluidos']}",
        fg="green" if execute else "yellow",
    )
