import click

from flask.cli import with_appcontext

from src.services.medicos_spdata_service import (
    buscar_medicos_spdata,
    upsert_usuario_medico_spdata,
)
from src.services.unidades_service import vincular_usuario_unidade
from src.settings.extensions import db


def exibir_opcoes_medicos(medicos):
    click.echo("Mais de um médico encontrado no SPDATA:")

    for medico in medicos:
        click.echo(
            "  "
            f"ID={medico.get('ID')} | "
            f"NOME={medico.get('NOME')} | "
            f"CPF={medico.get('CPF') or medico.get('CNPJ_CPF')} | "
            f"CRM={medico.get('OLD_CRM') or '-'} | "
            f"CRM_ATENDIMENTO={medico.get('CRM_ATENDIMENTO_SPDATA') or '-'}"
        )


@click.command("registrar-medico-spdata")
@click.option("--spdata-id", type=int, help="ID do médico na TBPROFIS.")
@click.option("--cpf", help="CPF/CNPJ_CPF do médico na TBPROFIS.")
@click.option("--nome", help="Trecho do nome do médico na TBPROFIS.")
@click.option("--email", help="E-mail de login. Se omitido, usa EMAIL_CONSULTORIO/EMAIL do SPDATA.")
@click.option(
    "--crm-atendimento-spdata",
    help="Sobrescreve o TBCBOPRO.COD usado para filtrar a agenda do médico.",
)
@click.option(
    "--senha",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Senha inicial do usuário local.",
)
@click.option(
    "--unidade-id",
    multiple=True,
    type=int,
    help="ID local da unidade vinculada ao médico. Pode ser repetido.",
)
@with_appcontext
def registrar_medico_spdata_command(spdata_id, cpf, nome, email, crm_atendimento_spdata, senha, unidade_id):
    """Registra no banco local um médico existente no SPDATA."""

    filtros = [bool(spdata_id), bool(cpf), bool(nome)]
    if sum(filtros) != 1:
        raise click.ClickException("Use apenas um filtro: --spdata-id, --cpf ou --nome.")

    medicos_spdata = buscar_medicos_spdata(
        spdata_id=spdata_id,
        cpf=cpf,
        nome=nome,
    )

    if not medicos_spdata:
        raise click.ClickException("Médico não encontrado no SPDATA.")

    if len(medicos_spdata) > 1:
        exibir_opcoes_medicos(medicos_spdata)
        raise click.ClickException("Refaça o comando usando --spdata-id para escolher um médico.")

    try:
        resultado = upsert_usuario_medico_spdata(
            medicos_spdata[0],
            email=email,
            senha=senha,
            crm_atendimento_spdata=crm_atendimento_spdata,
        )
        usuario = resultado["usuario"]
        medico = resultado["medico"]
        usuario_criado = resultado["usuario_criado"]
        medico_criado = resultado["medico_criado"]
        dados = resultado["dados"]

        for indice, unidade in enumerate(unidade_id):
            vincular_usuario_unidade(usuario.id, int(unidade), principal=indice == 0)
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        raise click.ClickException(f"Falha ao registrar médico: {exc}") from exc

    click.secho("Médico registrado com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id} ({'criado' if usuario_criado else 'atualizado'})")
    click.echo(f"  medico_id: {medico.id} ({'criado' if medico_criado else 'atualizado'})")
    click.echo(f"  spdata_id: {dados['spdata_id']}")
    click.echo(f"  nome: {dados['nome_completo']}")
    click.echo(f"  email: {dados['email']}")
    click.echo(f"  crm: {dados['crm'] or '-'}")
    click.echo(f"  crm_atendimento_spdata: {dados['crm_atendimento_spdata'] or '-'}")
    click.echo(f"  especialidade: {dados['especialidade'] or '-'}")
