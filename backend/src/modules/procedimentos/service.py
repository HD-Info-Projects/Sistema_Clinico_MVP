from sqlalchemy import String, cast, or_

from src.modules.procedimentos.models import Procedimento
from src.settings.extensions import db


def procedimento_para_dict(procedimento):
    return {
        "id": procedimento.id,
        "nome": procedimento.nome,
        "codigo_procedimento": procedimento.codigo_procedimento,
        "codigo_tuss": procedimento.proc_ref_tuss,
        "tipo_ato_codigo": procedimento.tipo_ato_codigo,
        "tipo_ato_nome": procedimento.tipo_ato_nome,
        "apelido_procedimento": procedimento.apelido_procedimento,
        "exige_autorizacao": procedimento.exige_autorizacao,
        "qtde_max_guia": procedimento.qtde_max_guia,
    }


def filtro_busca_procedimentos(q):
    like = f"%{q}%"
    return or_(
        Procedimento.nome.ilike(like),
        Procedimento.apelido_procedimento.ilike(like),
        Procedimento.tipo_ato_nome.ilike(like),
        cast(Procedimento.codigo_procedimento, String).ilike(like),
        cast(Procedimento.proc_ref_tuss, String).ilike(like),
    )


def buscar_procedimentos_catalogo(q, limit=50):
    q = (q or "").strip()
    if len(q) < 2:
        return []

    return (
        db.session.query(Procedimento)
        .filter(
            Procedimento.ativo.is_(True),
            filtro_busca_procedimentos(q),
        )
        .order_by(Procedimento.nome)
        .limit(limit)
        .all()
    )


__all__ = [
    "procedimento_para_dict",
    "filtro_busca_procedimentos",
    "buscar_procedimentos_catalogo",
]
