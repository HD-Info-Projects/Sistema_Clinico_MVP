from sqlalchemy import or_

from src.modules.exames.models import Exame
from src.settings.extensions import db


def exame_para_dict(exame):
    return {
        "id": exame.id,
        "nome": exame.nome,
        "codigo_alfanumerico": exame.codigo_alfanumerico,
        "codigo_amb": exame.codigo_amb,
    }


def filtro_busca_exames(q):
    like = f"%{q}%"
    return or_(
        Exame.nome.ilike(like),
        Exame.codigo_alfanumerico.ilike(like),
        Exame.codigo_amb.ilike(like),
    )


def listar_exames_catalogo():
    return db.session.query(Exame).order_by(Exame.nome).all()


def buscar_exames_catalogo(q, limit=50):
    q = (q or "").strip()
    if len(q) < 2:
        return []

    return (
        db.session.query(Exame)
        .filter(filtro_busca_exames(q))
        .order_by(Exame.nome)
        .limit(limit)
        .all()
    )


__all__ = [
    "exame_para_dict",
    "filtro_busca_exames",
    "listar_exames_catalogo",
    "buscar_exames_catalogo",
]
