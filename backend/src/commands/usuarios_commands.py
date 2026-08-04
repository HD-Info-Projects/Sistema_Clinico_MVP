import click

from flask.cli import with_appcontext

from src.models.usuario_model import Usuario
from src.security.passwords import validate_password_strength
from src.settings.extensions import db


def _registrar_usuario_local(nome_completo, documento, email, senha, role, atualizar):
    nome_completo = (nome_completo or "").strip()
    documento = (documento or "").strip()
    email = (email or "").strip().lower()

    if not nome_completo:
        raise click.ClickException("Informe --nome-completo.")
    if not documento:
        raise click.ClickException("Informe --documento.")
    if not email:
        raise click.ClickException("Informe --email.")
    if not senha:
        raise click.ClickException("Informe --senha.")

    try:
        validate_password_strength(senha)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    usuario = db.session.query(Usuario).filter(Usuario.email == email).first()

    if usuario and not atualizar:
        raise click.ClickException(
            "Já existe um usuário com esse e-mail. Use --atualizar para alterar."
        )

    try:
        if usuario is None:
            usuario = Usuario(
                nome_completo=nome_completo,
                cnpj_cpf=documento,
                email=email,
                senha=senha,
                role=role,
            )
            db.session.add(usuario)
            acao = "criado"
        else:
            usuario.nome_completo = nome_completo
            usuario.cnpj_cpf = documento
            usuario.set_senha(senha)
            usuario.role = role
            acao = "atualizado"

        db.session.commit()
        return usuario, acao

    except Exception as exc:
        db.session.rollback()
        raise click.ClickException(f"Falha ao registrar usuário: {exc}") from exc


@click.command("registrar-recepcao")
@click.option("--nome-completo", prompt=True, help="Nome completo do usuário da recepção.")
@click.option("--documento", prompt=True, help="CPF/CNPJ do usuário da recepção.")
@click.option("--email", prompt=True, help="E-mail usado no login.")
@click.option(
    "--senha",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Senha inicial do usuário da recepção.",
)
@click.option(
    "--atualizar",
    is_flag=True,
    help="Atualiza o usuário existente pelo e-mail, se ele já existir.",
)
@with_appcontext
def registrar_recepcao_command(nome_completo, documento, email, senha, atualizar):
    """Cria um usuário local com role recepcao."""

    usuario, acao = _registrar_usuario_local(
        nome_completo,
        documento,
        email,
        senha,
        "recepcao",
        atualizar,
    )

    click.secho("Usuário de recepção registrado com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id} ({acao})")
    click.echo(f"  nome: {usuario.nome_completo}")
    click.echo(f"  email: {usuario.email}")
    click.echo(f"  role: {usuario.role}")


@click.command("registrar-admin")
@click.option("--nome-completo", prompt=True, help="Nome completo do usuário admin.")
@click.option("--documento", prompt=True, help="CPF/CNPJ do usuário admin.")
@click.option("--email", prompt=True, help="E-mail usado no login.")
@click.option(
    "--senha",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Senha inicial do usuário admin.",
)
@click.option(
    "--atualizar",
    is_flag=True,
    help="Atualiza o usuário existente pelo e-mail, se ele já existir.",
)
@with_appcontext
def registrar_admin_command(nome_completo, documento, email, senha, atualizar):
    """Cria um usuário local com role admin."""

    usuario, acao = _registrar_usuario_local(
        nome_completo,
        documento,
        email,
        senha,
        "admin",
        atualizar,
    )

    click.secho("Usuário admin registrado com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id} ({acao})")
    click.echo(f"  nome: {usuario.nome_completo}")
    click.echo(f"  email: {usuario.email}")
    click.echo(f"  role: {usuario.role}")


@click.command("registrar-dpo")
@click.option("--nome-completo", prompt=True, help="Nome completo do usuário DPO.")
@click.option("--documento", prompt=True, help="CPF/CNPJ do usuário DPO.")
@click.option("--email", prompt=True, help="E-mail usado no login.")
@click.option(
    "--senha",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Senha inicial do usuário DPO.",
)
@click.option(
    "--atualizar",
    is_flag=True,
    help="Atualiza o usuário existente pelo e-mail, se ele já existir.",
)
@with_appcontext
def registrar_dpo_command(nome_completo, documento, email, senha, atualizar):
    """Cria um usuário local com role dpo para auditoria LGPD."""

    usuario, acao = _registrar_usuario_local(
        nome_completo,
        documento,
        email,
        senha,
        "dpo",
        atualizar,
    )

    click.secho("Usuário DPO registrado com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id} ({acao})")
    click.echo(f"  nome: {usuario.nome_completo}")
    click.echo(f"  email: {usuario.email}")
    click.echo(f"  role: {usuario.role}")
