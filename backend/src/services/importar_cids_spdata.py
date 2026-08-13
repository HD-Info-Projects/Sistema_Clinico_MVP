import logging

from sqlalchemy import select

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.model_mydsystem.med_spdata_cids_model import MedSpdataCid
from src.settings.extensions import db


logger = logging.getLogger(__name__)

MAX_CODIGO_LENGTH = 20
MAX_NOME_LENGTH = 255


def normalizar_texto(valor):
    if valor is None:
        return None

    valor = str(valor).strip()
    return valor or None


def normalizar_codigo_cid(valor):
    codigo = normalizar_texto(valor)
    if not codigo:
        return None

    codigo = codigo.upper()
    return codigo


def normalizar_nome_cid(valor):
    nome = normalizar_texto(valor)
    if not nome:
        return None

    return nome[:MAX_NOME_LENGTH]


def importar_cids_spdata(batch_size=200):
    total_lidos = 0
    total_criados = 0
    total_atualizados = 0
    total_inalterados = 0
    total_erros = 0
    total_duplicados = 0
    cids_processados = {}

    sql = """
        SELECT
            COD,
            NOME
        FROM TBCID10
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

                cids_lote = {}

                for row in rows:
                    total_lidos += 1

                    codigo = normalizar_codigo_cid(row[0])
                    nome_original = normalizar_texto(row[1])
                    nome = normalizar_nome_cid(row[1])

                    if not codigo:
                        total_erros += 1
                        logger.warning(
                            "CID ignorado sem COD. Linha: %s. COD=%r NOME=%r",
                            total_lidos,
                            row[0],
                            row[1],
                        )
                        continue

                    if len(codigo) > MAX_CODIGO_LENGTH:
                        total_erros += 1
                        logger.warning(
                            "CID ignorado com COD maior que %s caracteres. Linha: %s. COD=%r",
                            MAX_CODIGO_LENGTH,
                            total_lidos,
                            row[0],
                        )
                        continue

                    if not nome:
                        total_erros += 1
                        logger.warning(
                            "CID ignorado sem NOME. Linha: %s. COD=%r NOME=%r",
                            total_lidos,
                            row[0],
                            row[1],
                        )
                        continue

                    cid_processado = cids_processados.get(codigo)
                    if cid_processado:
                        if cid_processado != nome:
                            raise ValueError(
                                "CID duplicado na TBCID10 com descrições conflitantes: "
                                f"{codigo}"
                            )
                        total_duplicados += 1
                        continue

                    cids_processados[codigo] = nome

                    dados = {
                        "COD": codigo,
                        "NOME": nome_original,
                    }

                    cids_lote[codigo] = {
                        "codigo": codigo,
                        "nome": nome,
                        "dados_spdata": dados,
                    }

                codigos = list(cids_lote.keys())
                if not codigos:
                    continue

                existentes = db.session.execute(
                    select(MedSpdataCid).where(MedSpdataCid.codigo.in_(codigos))
                ).scalars().all()
                existentes_por_codigo = {cid.codigo: cid for cid in existentes}

                for codigo, dados in cids_lote.items():
                    cid = existentes_por_codigo.get(codigo)
                    if cid is None:
                        cid = MedSpdataCid(
                            codigo=dados["codigo"],
                            nome=dados["nome"],
                            dados_spdata=dados["dados_spdata"],
                        )
                        db.session.add(cid)
                        total_criados += 1
                        continue

                    if cid.nome != dados["nome"] or cid.dados_spdata != dados["dados_spdata"]:
                        cid.nome = dados["nome"]
                        cid.dados_spdata = dados["dados_spdata"]
                        total_atualizados += 1
                    else:
                        total_inalterados += 1

        if total_criados + total_atualizados + total_inalterados == 0:
            raise RuntimeError("Nenhum CID válido foi retornado pela TBCID10.")

        db.session.commit()

        return {
            "lidos": total_lidos,
            "criados": total_criados,
            "atualizados": total_atualizados,
            "inalterados": total_inalterados,
            "erros": total_erros,
            "duplicados": total_duplicados,
        }

    except Exception:
        db.session.rollback()
        logger.exception("Falha na importação da TBCID10.")
        raise
