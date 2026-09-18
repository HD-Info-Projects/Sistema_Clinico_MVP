import logging

from sqlalchemy import select

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.model_mydsystem.med_spdata_cids_model import MedSpdataCid
from src.settings.extensions import db


logger = logging.getLogger(__name__)


def normalizar_valor(valor):
    if valor is None:
        return None
    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.decode("cp1252", errors="replace")
    if hasattr(valor, "read"):
        return normalizar_valor(valor.read())
    return valor


def normalizar_texto(valor, limite=None):
    valor = normalizar_valor(valor)
    if valor is None:
        return None

    valor = str(valor).strip()
    if limite:
        valor = valor[:limite]

    return valor or None


def importar_cids_spdata(batch_size=200):
    total_lidos = 0
    total_criados = 0
    total_atualizados = 0
    total_erros = 0

    sql = """
        SELECT
            COD,
            NOME
        FROM TBCID10
        WHERE COD IS NOT NULL
          AND NOME IS NOT NULL
        ORDER BY COD
    """

    try:
        with ConnectionDBFireBird() as connection:
            cursor = connection.cursor()
            cursor.execute(sql)

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break

                codigos = {
                    codigo
                    for codigo, _ in (
                        (
                            normalizar_texto(row[0], 20),
                            normalizar_texto(row[1], 255),
                        )
                        for row in rows
                    )
                    if codigo
                }

                existentes = db.session.execute(
                    select(MedSpdataCid).where(MedSpdataCid.codigo.in_(codigos))
                ).scalars().all() if codigos else []
                existentes_por_codigo = {
                    cid.codigo: cid for cid in existentes
                }

                for row in rows:
                    total_lidos += 1

                    try:
                        codigo = normalizar_texto(row[0], 20)
                        nome = normalizar_texto(row[1], 255)

                        if not codigo or not nome:
                            total_erros += 1
                            logger.warning(
                                "CID ignorado sem código ou nome. Linha: %s",
                                total_lidos,
                            )
                            continue

                        cid = existentes_por_codigo.get(codigo)
                        if cid is None:
                            cid = MedSpdataCid(codigo=codigo, nome=nome)
                            db.session.add(cid)
                            existentes_por_codigo[codigo] = cid
                            total_criados += 1
                        else:
                            total_atualizados += 1

                        cid.nome = nome
                        cid.dados_spdata = {
                            "COD": codigo,
                            "NOME": nome,
                        }
                    except Exception:
                        total_erros += 1
                        logger.exception(
                            "Erro processando CID do SPDATA. Linha: %s",
                            total_lidos,
                        )

                db.session.commit()

        return {
            "lidos": total_lidos,
            "criados": total_criados,
            "atualizados": total_atualizados,
            "erros": total_erros,
        }
    except Exception:
        db.session.rollback()
        logger.exception("Falha na importação da TBCID10.")
        raise
