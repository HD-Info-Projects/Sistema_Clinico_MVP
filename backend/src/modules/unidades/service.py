import re
import unicodedata

from sqlalchemy import or_, select

from src.models.usuario_model import Usuario
from src.modules.unidades.models import Unidade, UsuarioUnidade
from src.settings.extensions import db


class UnidadePayloadError(ValueError):
    def __init__(self, message, fields):
        super().__init__(message)
        self.message = message
        self.fields = fields


def normalizar_texto(valor, limite=None):
    if valor is None:
        return None

    texto = str(valor).strip()
    if limite:
        texto = texto[:limite]
    return texto or None


def _normalizar_int(valor):
    if valor is None or valor == "":
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _bool_payload(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in {"1", "true", "sim", "s", "yes"}
    return bool(valor)


def gerar_slug(nome):
    texto = normalizar_texto(nome, 120) or "unidade"
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    texto = texto.strip("-")
    return texto or "unidade"


def _slug_base(nome):
    texto = unicodedata.normalize("NFKD", nome)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return (texto or "unidade")[:120].strip("-") or "unidade"


def _slug_unico(nome, unidade_id=None):
    base = _slug_base(nome)
    slug = base
    contador = 2

    while True:
        query = select(Unidade).where(Unidade.slug == slug)
        if unidade_id is not None:
            query = query.where(Unidade.id != unidade_id)
        existente = db.session.execute(query).scalars().first()
        if not existente:
            return slug

        sufixo = f"-{contador}"
        slug = f"{base[:120 - len(sufixo)].rstrip('-')}{sufixo}"
        contador += 1


def _aplicar_payload(unidade, data, criar=False):
    nome = normalizar_texto(data.get("nome"), 255)
    if not nome:
        raise UnidadePayloadError("Campos obrigatórios ausentes.", ["nome"])

    codigo_spdata_centro_custo = _normalizar_int(data.get("codigo_spdata_centro_custo"))
    codigo_spdata_agenda = normalizar_texto(data.get("codigo_spdata_agenda"), 50)
    campos_invalidos = []
    if codigo_spdata_centro_custo is None:
        campos_invalidos.append("codigo_spdata_centro_custo")
    if not codigo_spdata_agenda:
        campos_invalidos.append("codigo_spdata_agenda")
    if campos_invalidos:
        raise UnidadePayloadError(
            "Campos obrigatórios ausentes ou inválidos.",
            campos_invalidos,
        )

    unidade.nome = nome
    unidade.slug = _slug_unico(nome, unidade_id=unidade.id)
    unidade.codigo_spdata_centro_custo = codigo_spdata_centro_custo
    unidade.codigo_spdata_agenda = codigo_spdata_agenda
    unidade.endereco = normalizar_texto(data.get("endereco"), 500)
    unidade.telefone = normalizar_texto(data.get("telefone"), 50)
    if criar or "ativa" in data:
        unidade.ativa = _bool_payload(data.get("ativa", True))


def listar_unidades_admin():
    return db.session.execute(
        select(Unidade).order_by(Unidade.nome.asc())
    ).scalars().all()


def criar_unidade(data):
    unidade = Unidade()
    _aplicar_payload(unidade, data, criar=True)
    db.session.add(unidade)
    db.session.commit()
    return unidade


def atualizar_unidade(unidade_id, data):
    unidade = db.session.get(Unidade, unidade_id)
    if not unidade:
        return None

    _aplicar_payload(unidade, data)
    db.session.commit()
    return unidade


def inativar_unidade(unidade_id):
    unidade = db.session.get(Unidade, unidade_id)
    if not unidade:
        return None

    unidade.ativa = False
    db.session.commit()
    return unidade


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


def listar_unidades_ativas_frontend():
    unidades = (
        db.session.execute(
            select(Unidade)
            .where(Unidade.ativa.is_(True))
            .order_by(Unidade.nome.asc())
        )
        .scalars()
        .all()
    )
    return [unidade._to_frontend_dict() for unidade in unidades]


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
    usuario = db.session.get(Usuario, usuario_id)

    if usuario is not None and usuario.role == "admin":
        if unidade_id is None:
            raise PermissionError("Unidade ativa obrigatória")

        unidade_admin = db.session.execute(
            select(Unidade).where(
                Unidade.id == unidade_id,
                Unidade.ativa.is_(True),
            )
        ).scalar_one_or_none()

        if not unidade_admin:
            raise PermissionError("Usuário não possui acesso à unidade informada")

        return unidade_admin

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


__all__ = [
    "UnidadePayloadError",
    "normalizar_texto",
    "gerar_slug",
    "listar_unidades_admin",
    "criar_unidade",
    "atualizar_unidade",
    "inativar_unidade",
    "listar_unidades_usuario",
    "listar_unidades_usuario_frontend",
    "listar_unidades_ativas_frontend",
    "normalizar_unidade_ids",
    "validar_unidades_ativas",
    "sincronizar_unidades_usuario",
    "buscar_unidade_publica",
    "resolver_unidade_usuario",
    "vincular_usuario_unidade",
]
