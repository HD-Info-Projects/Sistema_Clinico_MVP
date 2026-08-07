import re

from sqlalchemy import or_, select

from src.models.unidade_model import Unidade
from src.models.usuario_unidade_model import UsuarioUnidade
from src.settings.extensions import db


def normalizar_texto(valor, limite=None):
    if valor is None:
        return None

    texto = str(valor).strip()
    if limite:
        texto = texto[:limite]
    return texto or None


def gerar_slug(nome):
    texto = normalizar_texto(nome, 120) or "unidade"
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    texto = texto.strip("-")
    return texto or "unidade"


def listar_unidades_usuario(usuario_id):
    vinculos = (
        db.session.query(UsuarioUnidade)
        .join(Unidade, Unidade.id == UsuarioUnidade.unidade_id)
        .filter(
            UsuarioUnidade.usuario_id == usuario_id,
            UsuarioUnidade.ativo.is_(True),
            Unidade.ativa.is_(True),
        )
        .order_by(UsuarioUnidade.principal.desc(), Unidade.nome)
        .all()
    )
    return [vinculo.unidade for vinculo in vinculos]


def listar_unidades_usuario_frontend(usuario_id):
    return [unidade._to_frontend_dict() for unidade in listar_unidades_usuario(usuario_id)]


def buscar_unidade_publica(identificador):
    if identificador is None:
        return None

    texto = str(identificador).strip()
    if not texto:
        return None

    filtros = [Unidade.slug == texto]
    try:
        filtros.append(Unidade.id == int(texto))
    except ValueError:
        pass

    return db.session.execute(
        select(Unidade).where(
            Unidade.ativa.is_(True),
            or_(*filtros),
        )
    ).scalars().first()


def resolver_unidade_usuario(usuario_id, unidade_id=None):
    query = (
        db.session.query(UsuarioUnidade)
        .join(Unidade, Unidade.id == UsuarioUnidade.unidade_id)
        .filter(
            UsuarioUnidade.usuario_id == usuario_id,
            UsuarioUnidade.ativo.is_(True),
            Unidade.ativa.is_(True),
        )
    )

    if unidade_id is not None:
        query = query.filter(UsuarioUnidade.unidade_id == unidade_id)
        vinculo = query.first()
        if not vinculo:
            raise PermissionError("Usuário não possui acesso à unidade informada")
        return vinculo.unidade

    vinculo = query.order_by(UsuarioUnidade.principal.desc(), Unidade.nome).first()
    if not vinculo:
        raise PermissionError("Usuário não possui unidade vinculada")

    return vinculo.unidade


def vincular_usuario_unidade(usuario_id, unidade_id, principal=False):
    unidade = db.session.get(Unidade, unidade_id)
    if not unidade or not unidade.ativa:
        raise ValueError("Unidade inválida")

    vinculo = db.session.execute(
        select(UsuarioUnidade).where(
            UsuarioUnidade.usuario_id == usuario_id,
            UsuarioUnidade.unidade_id == unidade_id,
        )
    ).scalars().first()

    if vinculo is None:
        vinculo = UsuarioUnidade(
            usuario_id=usuario_id,
            unidade_id=unidade_id,
            principal=principal,
            ativo=True,
        )
        db.session.add(vinculo)
    else:
        vinculo.ativo = True
        vinculo.principal = principal or vinculo.principal

    if principal:
        db.session.query(UsuarioUnidade).filter(
            UsuarioUnidade.usuario_id == usuario_id,
            UsuarioUnidade.unidade_id != unidade_id,
        ).update({UsuarioUnidade.principal: False})

    return vinculo
