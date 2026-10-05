import click

from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy.orm import joinedload

from src.models.medico_model import Medico
from src.models.usuario_model import Usuario
from src.security.passwords import is_hashed_password, validate_password_strength
from src.security.roles import ROLE_ASSISTENTE, ROLE_MEDICO
from src.modules.unidades.service import vincular_usuario_unidade
from src.settings.extensions import db


def _password_min_length():
    return int(current_app.config.get("PASSWORD_MIN_LENGTH", 6))


def _buscar_usuario(usuario_id=None, email=None):
    if usuario_id is not None:
        usuario = db.session.get(Usuario, int(usuario_id))
    else:
        email = (email or "").strip().lower()
        usuario = db.session.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        raise click.ClickException("Usuário não encontrado.")

    return usuario


def _iter_usuarios_senhas_legadas():
    query = db.session.query(Usuario).order_by(Usuario.id)
    for usuario in query.yield_per(200):
        if not is_hashed_password(usuario.senha):
            yield usuario


def _registrar_usuario_local(
    nome_completo,
    documento,
    email,
    senha,
    role,
    atualizar,
    unidade_ids=None,
    medico_assistente_id=None,
):
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
        validate_password_strength(senha, _password_min_length())
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
            usuario.desbloquear()
            acao = "atualizado"

        usuario.medico_assistente_id = (
            medico_assistente_id if role == ROLE_ASSISTENTE else None
        )

        db.session.flush()
        for indice, unidade_id in enumerate(unidade_ids or []):
            vincular_usuario_unidade(usuario.id, int(unidade_id), principal=indice == 0)

        db.session.commit()
        return usuario, acao

    except Exception as exc:
        db.session.rollback()
        raise click.ClickException(f"Falha ao registrar usuário: {exc}") from exc


def _validar_medico_assistente(medico_id, usuario_id=None):
    medico = (
        db.session.query(Medico)
        .options(joinedload(Medico.usuario))
        .filter(Medico.id == int(medico_id))
        .first()
    )

    if not medico:
        raise click.ClickException("Médico vinculado ao assistente não encontrado.")
    if not medico.ativo:
        raise click.ClickException("Médico vinculado ao assistente está inativo.")
    if not medico.usuario or medico.usuario.role != ROLE_MEDICO:
        raise click.ClickException("Assistente deve ser vinculado a um usuário médico cadastrado.")
    if usuario_id is not None and medico.usuario_id == usuario_id:
        raise click.ClickException("Assistente não pode ser vinculado ao próprio usuário.")
    if not str(medico.crm_atendimento_spdata or medico.crm or "").strip():
        raise click.ClickException("Médico vinculado não possui CRM configurado para filtrar agenda.")

    return medico


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
@click.option(
    "--unidade-id",
    multiple=True,
    type=int,
    help="ID local da unidade vinculada ao usuário. Pode ser repetido.",
)
@with_appcontext
def registrar_recepcao_command(nome_completo, documento, email, senha, atualizar, unidade_id):
    """Cria um usuário local com role recepcao."""

    usuario, acao = _registrar_usuario_local(
        nome_completo,
        documento,
        email,
        senha,
        "recepcao",
        atualizar,
        unidade_ids=unidade_id,
    )

    click.secho("Usuário de recepção registrado com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id} ({acao})")
    click.echo(f"  nome: {usuario.nome_completo}")
    click.echo(f"  email: {usuario.email}")
    click.echo(f"  role: {usuario.role}")


@click.command("registrar-assistente")
@click.option("--nome-completo", prompt=True, help="Nome completo do assistente.")
@click.option("--documento", prompt=True, help="CPF/CNPJ do assistente.")
@click.option("--email", prompt=True, help="E-mail usado no login.")
@click.option(
    "--senha",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Senha inicial do assistente.",
)
@click.option(
    "--medico-id",
    required=True,
    type=int,
    help="ID local da tabela medicos que o assistente vai auxiliar.",
)
@click.option(
    "--atualizar",
    is_flag=True,
    help="Atualiza o usuário existente pelo e-mail, se ele já existir.",
)
@click.option(
    "--unidade-id",
    multiple=True,
    type=int,
    required=True,
    help="ID local da unidade vinculada ao assistente. Pode ser repetido.",
)
@with_appcontext
def registrar_assistente_command(nome_completo, documento, email, senha, medico_id, atualizar, unidade_id):
    """Cria um usuário local com role assistente vinculado a um médico."""

    medico = _validar_medico_assistente(medico_id)
    email_normalizado = (email or "").strip().lower()
    usuario_existente = db.session.query(Usuario).filter(Usuario.email == email_normalizado).first()
    if usuario_existente:
        _validar_medico_assistente(medico_id, usuario_id=usuario_existente.id)

    usuario, acao = _registrar_usuario_local(
        nome_completo,
        documento,
        email,
        senha,
        ROLE_ASSISTENTE,
        atualizar,
        unidade_ids=unidade_id,
        medico_assistente_id=medico.id,
    )

    click.secho("Usuário assistente registrado com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id} ({acao})")
    click.echo(f"  nome: {usuario.nome_completo}")
    click.echo(f"  email: {usuario.email}")
    click.echo(f"  role: {usuario.role}")
    click.echo(f"  medico_id: {medico.id}")
    click.echo(f"  medico: {medico.usuario.nome_completo if medico.usuario else ''}")
    click.echo(f"  crm: {medico.crm_atendimento_spdata or medico.crm}")


@click.command("usuarios-senhas-legadas")
@click.option(
    "--limit",
    default=100,
    show_default=True,
    type=click.IntRange(min=1, max=10000),
    help="Quantidade máxima de usuários exibidos no relatório.",
)
@click.option(
    "--fail-on-found",
    is_flag=True,
    help="Retorna erro se houver ao menos uma senha legada.",
)
@with_appcontext
def usuarios_senhas_legadas_command(limit, fail_on_found):
    """Lista usuários com senha legada sem expor a senha."""

    total = 0
    exibidos = []

    for usuario in _iter_usuarios_senhas_legadas():
        total += 1
        if len(exibidos) < limit:
            exibidos.append(usuario)

    click.echo(f"Usuários com senha legada: {total}")
    for usuario in exibidos:
        click.echo(
            "  "
            f"id={usuario.id} "
            f"email={usuario.email} "
            f"role={usuario.role} "
            f"ativo={bool(usuario.ativo)} "
            f"bloqueado={usuario.bloqueado_em is not None}"
        )

    if total > len(exibidos):
        click.echo(f"  ... {total - len(exibidos)} usuários omitidos pelo limite.")

    if total:
        click.secho(
            "Ação recomendada: redefinir essas senhas com resetar-senha-usuario antes de remover o fallback legado.",
            fg="yellow",
        )

    if fail_on_found and total:
        raise click.ClickException("Foram encontradas senhas legadas.")


@click.command("resetar-senha-usuario")
@click.option("--usuario-id", type=int, help="ID local do usuário.")
@click.option("--email", help="E-mail do usuário.")
@click.option(
    "--senha",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Nova senha do usuário.",
)
@click.option(
    "--manter-bloqueio",
    is_flag=True,
    help="Mantém bloqueio atual mesmo após redefinir a senha.",
)
@with_appcontext
def resetar_senha_usuario_command(usuario_id, email, senha, manter_bloqueio):
    """Redefine senha com hash forte e limpa contadores de falha."""

    if bool(usuario_id) == bool(email):
        raise click.ClickException("Informe exatamente um identificador: --usuario-id ou --email.")

    try:
        validate_password_strength(senha, _password_min_length())
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    usuario = _buscar_usuario(usuario_id=usuario_id, email=email)
    usuario.set_senha(senha)
    if not manter_bloqueio:
        usuario.desbloquear()

    db.session.commit()

    click.secho("Senha redefinida com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id}")
    click.echo(f"  email: {usuario.email}")
    click.echo(f"  role: {usuario.role}")
    click.echo(f"  bloqueado: {usuario.bloqueado_em is not None}")


@click.command("desbloquear-usuario")
@click.option("--usuario-id", type=int, help="ID local do usuário.")
@click.option("--email", help="E-mail do usuário.")
@with_appcontext
def desbloquear_usuario_command(usuario_id, email):
    """Remove bloqueio e limpa contadores de tentativas falhas."""

    if bool(usuario_id) == bool(email):
        raise click.ClickException("Informe exatamente um identificador: --usuario-id ou --email.")

    usuario = _buscar_usuario(usuario_id=usuario_id, email=email)
    usuario.desbloquear()
    db.session.commit()

    click.secho("Usuário desbloqueado com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id}")
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
@click.option(
    "--unidade-id",
    multiple=True,
    type=int,
    help="ID local da unidade vinculada ao usuário. Pode ser repetido.",
)
@with_appcontext
def registrar_admin_command(nome_completo, documento, email, senha, atualizar, unidade_id):
    """Cria um usuário local com role admin."""

    usuario, acao = _registrar_usuario_local(
        nome_completo,
        documento,
        email,
        senha,
        "admin",
        atualizar,
        unidade_ids=unidade_id,
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
