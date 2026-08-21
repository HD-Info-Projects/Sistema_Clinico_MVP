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


def normalizar_unidade_ids(unidade_ids):
    if unidade_ids is None or unidade_ids == "":
        return []

    if isinstance(unidade_ids, (str, int)):
        unidade_ids = [unidade_ids]

    ids_normalizados = []
    for unidade_id in unidade_ids:
        try:
            unidade_id = int(unidade_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("Unidade inválida") from exc

        if unidade_id <= 0:
            raise ValueError("Unidade inválida")
        if unidade_id not in ids_normalizados:
            ids_normalizados.append(unidade_id)

    return ids_normalizados


def validar_unidades_ativas(unidade_ids):
    unidade_ids = normalizar_unidade_ids(unidade_ids)
    if not unidade_ids:
        return []

    unidades = db.session.execute(
        select(Unidade).where(
            Unidade.id.in_(unidade_ids),
            Unidade.ativa.is_(True),
        )
    ).scalars().all()
    unidades_por_id = {unidade.id: unidade for unidade in unidades}

    if any(unidade_id not in unidades_por_id for unidade_id in unidade_ids):
        raise ValueError("Unidade inválida")

    return [unidades_por_id[unidade_id] for unidade_id in unidade_ids]


def sincronizar_unidades_usuario(usuario_id, unidade_ids):
    unidade_ids = normalizar_unidade_ids(unidade_ids)
    validar_unidades_ativas(unidade_ids)

    vinculos = db.session.execute(
        select(UsuarioUnidade).where(UsuarioUnidade.usuario_id == usuario_id)
    ).scalars().all()
    vinculos_por_unidade = {vinculo.unidade_id: vinculo for vinculo in vinculos}
    ids_selecionados = set(unidade_ids)

    for vinculo in vinculos:
        if vinculo.unidade_id not in ids_selecionados:
            vinculo.ativo = False
            vinculo.principal = False

    for indice, unidade_id in enumerate(unidade_ids):
        vinculo = vinculos_por_unidade.get(unidade_id)
        if vinculo is None:
            vinculo = UsuarioUnidade(
                usuario_id=usuario_id,
                unidade_id=unidade_id,
            )
            db.session.add(vinculo)

        vinculo.ativo = True
        vinculo.principal = indice == 0

    return unidade_ids


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

    vinculos = query.order_by(UsuarioUnidade.principal.desc(), Unidade.nome).all()
    if not vinculos:
        raise PermissionError("Usuário não possui unidade vinculada")
    if len(vinculos) > 1:
        raise PermissionError("Unidade ativa obrigatória")

    return vinculos[0].unidade


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
        vinculo.principal = bool(principal)

    if principal:
        db.session.query(UsuarioUnidade).filter(
            UsuarioUnidade.usuario_id == usuario_id,
            UsuarioUnidade.unidade_id != unidade_id,
        ).update({UsuarioUnidade.principal: False})

    return vinculo
