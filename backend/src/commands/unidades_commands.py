import click
from flask.cli import with_appcontext

from src.models.unidade_model import Unidade
from src.models.usuario_model import Usuario
from src.services.unidades_service import gerar_slug, vincular_usuario_unidade
from src.settings.extensions import db


@click.command("criar-unidade")
@click.option("--nome", prompt=True, help="Nome da unidade exibido no sistema.")
@click.option("--slug", help="Identificador público opcional da unidade.")
@click.option("--codigo-spdata-centro-custo", type=int, help="Código SPDATA ATCABECATEND.ID_TBCENCUS.")
@click.option("--codigo-spdata-agenda", help="Código SPDATA REPACAGD.UNIDADE.")
@click.option("--endereco", help="Endereço exibido no frontend.")
@click.option("--telefone", help="Telefone exibido no frontend.")
@with_appcontext
def criar_unidade_command(nome, slug, codigo_spdata_centro_custo, codigo_spdata_agenda, endereco, telefone):
    slug = slug or gerar_slug(nome)

    existente = db.session.query(Unidade).filter(Unidade.slug == slug).first()
    if existente:
        raise click.ClickException("Já existe uma unidade com esse slug.")

    unidade = Unidade(
        nome=nome.strip(),
        slug=slug,
        codigo_spdata_centro_custo=codigo_spdata_centro_custo,
        codigo_spdata_agenda=str(codigo_spdata_agenda).strip() if codigo_spdata_agenda else None,
        endereco=(endereco or "").strip() or None,
        telefone=(telefone or "").strip() or None,
        ativa=True,
    )
    db.session.add(unidade)
    db.session.commit()

    click.secho("Unidade criada com sucesso.", fg="green")
    click.echo(f"  unidade_id: {unidade.id}")
    click.echo(f"  nome: {unidade.nome}")


@click.command("listar-unidades")
@with_appcontext
def listar_unidades_command():
    unidades = db.session.query(Unidade).order_by(Unidade.nome).all()
    for unidade in unidades:
        status = "ativa" if unidade.ativa else "inativa"
        click.echo(
            f"ID={unidade.id} | {unidade.nome} | {status} | "
            f"centro_custo={unidade.codigo_spdata_centro_custo or '-'} | "
            f"agenda={unidade.codigo_spdata_agenda or '-'}"
        )


@click.command("vincular-unidade-usuario")
@click.option("--email", required=True, help="E-mail do usuário.")
@click.option("--unidade-id", required=True, type=int, help="ID local da unidade.")
@click.option("--principal", is_flag=True, help="Define esta unidade como principal do usuário.")
@with_appcontext
def vincular_unidade_usuario_command(email, unidade_id, principal):
    usuario = db.session.query(Usuario).filter(Usuario.email == email.strip().lower()).first()
    if not usuario:
        raise click.ClickException("Usuário não encontrado.")

    vincular_usuario_unidade(usuario.id, unidade_id, principal=principal)
    db.session.commit()

    click.secho("Usuário vinculado à unidade com sucesso.", fg="green")
    click.echo(f"  usuario_id: {usuario.id}")
    click.echo(f"  unidade_id: {unidade_id}")
