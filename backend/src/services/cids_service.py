from src.models.model_mydsystem.med_spdata_cids_model import MedSpdataCid


def escape_like(valor):
    return (
        valor.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def buscar_cids_locais(q, limit=20, offset=0, is_codigo_cid=False):
    q = (q or "").strip()
    limit = min(max(limit or 20, 1), 50)
    offset = max(offset or 0, 0)

    if not q:
        return {
            "items": [],
            "limit": limit,
            "offset": offset,
            "has_more": False,
        }

    if is_codigo_cid:
        termo = escape_like(q.upper())
        filtro = MedSpdataCid.codigo.like(f"{termo}%", escape="\\")
    else:
        termo = escape_like(q)
        filtro = MedSpdataCid.nome.ilike(f"%{termo}%", escape="\\")

    cids = (
        MedSpdataCid.query.filter(filtro)
        .order_by(MedSpdataCid.codigo.asc())
        .offset(offset)
        .limit(limit + 1)
        .all()
    )

    items = [
        {
            "CID": cid.codigo,
            "DOENCA": cid.nome,
        }
        for cid in cids[:limit]
    ]

    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "has_more": len(cids) > limit,
    }
