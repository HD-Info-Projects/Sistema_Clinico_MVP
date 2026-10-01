# src/services/importar_exames_spdata.py

import json
import logging

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import select

from src.settings.extensions import db
from src.models.model_mydsystem.med_exames_model import Exame
from src.models.db.handler_fb_db import ConnectionDBFireBird


logger = logging.getLogger(__name__)


COLUNAS_SITABPRO = [
    "ID",
    "ATO",
    "CODALF",
    "NOME",
    "CODAMB",
    "EQVAMB",
    "EQVAIH",
    "GRUPO",
    "UNID",
    "REFINI",
    "REFFIN",
    "TIPO",
    "VARIAVEL",
    "SEQ",
    "ENTREGA",
    "CASAS",
    "COLETOR",
    "METODO",
    "ALFANUM",
    "VLRREF",
    "NCOMUM",
    "PREPAR",
    "INCID",
    "MATERIAL",
    "ULTRASON",
    "RESSON",
    "ENTHORS",
    "REFIDADE",
    "TPAIH",
    "SITUACAO",
    "TIPO_PROC",
    "DUM",
    "RECIPIENTE",
    "IMP_ELE_MAPA",
    "MIN_ABE",
    "MAX_ABE",
    "PROCESPECIAL",
    "ID_TBPROSUSAIH",
    "ID_TBPROSUSAMB",
    "IMPCCIH",
    "NOTIFICACAOCOMP",
    "PERIODOVENC",
    "VLRREF2",
    "SEQPESQUISA",
    "INTEGRAR_VEPRO",
    "IMPRIMIR_ETIQUETA_TRIAGEM",
    "ID_SIPACSMODALID",
    "TORNAR_INF_COMP_CLIN_OBRIG_PEP",
    "EXAME_INTEGRADO_WEBSERVICE",
    "ANTIBIOGRAMA",
    "ID_TBSEXO",
    "ID_PRTIPONOTIFICACAO",
    "IDADEI",
    "IDADEF",
    "ID_PRTIPONOTIFICACAOIDADE",
    "ID_TBUNID_IDADE_MIN",
    "ID_TBUNID_IDADE_MAX",
    "ID_DIGITAL_OBS_IDE_LOC",
    "ID_DIGITAL_OBS_IDE",
    "SOMENTE_SOLICITACAO_PEP",
    "EXIBIR_FICHA_ANEST",
    "ORDEM_FICHA_ANEST",
]


def normalizar_valor(valor):
    """
    Converte valores do Firebird para tipos aceitos pelo JSON/MySQL.
    """

    if valor is None:
        return None

    if isinstance(valor, Decimal):
        return float(valor)

    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()

    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.hex()

    # Alguns drivers podem retornar objetos BLOB com read()
    if hasattr(valor, "read"):
        conteudo = valor.read()

        if isinstance(conteudo, bytes):
            try:
                return conteudo.decode("utf-8")
            except UnicodeDecodeError:
                return conteudo.hex()

        return str(conteudo)

    return valor


def normalizar_texto(valor, limite=None):
    if valor is None:
        return None

    valor = str(valor).strip()

    if limite:
        valor = valor[:limite]

    return valor or None


def row_para_dict(row, nomes_colunas):
    return {
        nome: normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def importar_exames_spdata(batch_size=200, on_progress=None):
    total_lidos = 0
    total_criados = 0
    total_atualizados = 0
    total_erros = 0

    sql = """
        SELECT
            ID,
            ATO,
            CODALF,
            NOME,
            CODAMB,
            EQVAMB,
            EQVAIH,
            GRUPO,
            UNID,
            REFINI,
            REFFIN,
            TIPO,
            VARIAVEL,
            SEQ,
            ENTREGA,
            CASAS,
            COLETOR,
            METODO,
            ALFANUM,
            VLRREF,
            NCOMUM,
            PREPAR,
            INCID,
            MATERIAL,
            ULTRASON,
            RESSON,
            ENTHORS,
            REFIDADE,
            TPAIH,
            SITUACAO,
            TIPO_PROC,
            DUM,
            RECIPIENTE,
            IMP_ELE_MAPA,
            MIN_ABE,
            MAX_ABE,
            PROCESPECIAL,
            ID_TBPROSUSAIH,
            ID_TBPROSUSAMB,
            IMPCCIH,
            NOTIFICACAOCOMP,
            PERIODOVENC,
            VLRREF2,
            SEQPESQUISA,
            INTEGRAR_VEPRO,
            IMPRIMIR_ETIQUETA_TRIAGEM,
            ID_SIPACSMODALID,
            TORNAR_INF_COMP_CLIN_OBRIG_PEP,
            EXAME_INTEGRADO_WEBSERVICE,
            ANTIBIOGRAMA,
            ID_TBSEXO,
            ID_PRTIPONOTIFICACAO,
            IDADEI,
            IDADEF,
            ID_PRTIPONOTIFICACAOIDADE,
            ID_TBUNID_IDADE_MIN,
            ID_TBUNID_IDADE_MAX,
            ID_DIGITAL_OBS_IDE_LOC,
            ID_DIGITAL_OBS_IDE,
            SOMENTE_SOLICITACAO_PEP,
            EXIBIR_FICHA_ANEST,
            ORDEM_FICHA_ANEST
        FROM SITABPRO
        ORDER BY ID
    """

    try:
        with ConnectionDBFireBird() as connection:
            cursor = connection.cursor()
            cursor.execute(sql)

            nomes_colunas = [
                descricao[0].strip().upper()
                for descricao in cursor.description
            ]

            while True:
                rows = cursor.fetchmany(batch_size)

                if not rows:
                    break

                ids_spdata = [
                    row[0]
                    for row in rows
                    if row[0] is not None
                ]

                existentes = db.session.execute(
                    select(Exame).where(
                        Exame.spdata_id.in_(ids_spdata)
                    )
                ).scalars().all()

                existentes_por_id = {
                    exame.spdata_id: exame
                    for exame in existentes
                }

                for row in rows:
                    total_lidos += 1

                    try:
                        dados = row_para_dict(row, nomes_colunas)

                        spdata_id = dados.get("ID")
                        nome = normalizar_texto(dados.get("NOME"), 255)

                        if spdata_id is None:
                            logger.warning(
                                "Registro ignorado porque não possui ID."
                            )
                            total_erros += 1
                            continue

                        if not nome:
                            nome = f"Exame SPDATA {spdata_id}"

                        exame = existentes_por_id.get(spdata_id)

                        if exame is None:
                            exame = Exame(spdata_id=spdata_id)
                            db.session.add(exame)
                            existentes_por_id[spdata_id] = exame
                            total_criados += 1
                        else:
                            total_atualizados += 1

                        exame.ato = normalizar_texto(
                            dados.get("ATO"),
                            50,
                        )

                        exame.codigo_alfanumerico = normalizar_texto(
                            dados.get("CODALF"),
                            100,
                        )

                        exame.nome = nome

                        exame.codigo_amb = normalizar_texto(
                            dados.get("CODAMB"),
                            100,
                        )

                        exame.grupo = normalizar_texto(
                            dados.get("GRUPO"),
                            100,
                        )

                        exame.unidade = normalizar_texto(
                            dados.get("UNID"),
                            100,
                        )

                        exame.tipo = normalizar_texto(
                            dados.get("TIPO"),
                            50,
                        )

                        exame.tipo_procedimento = normalizar_texto(
                            dados.get("TIPO_PROC"),
                            50,
                        )

                        exame.material = normalizar_texto(
                            dados.get("MATERIAL"),
                            255,
                        )

                        exame.metodo = normalizar_texto(
                            dados.get("METODO"),
                        )

                        exame.preparacao = normalizar_texto(
                            dados.get("PREPAR"),
                        )

                        exame.coletor = normalizar_texto(
                            dados.get("COLETOR"),
                            255,
                        )

                        exame.entrega = normalizar_texto(
                            dados.get("ENTREGA"),
                            100,
                        )

                        exame.recipiente = normalizar_texto(
                            dados.get("RECIPIENTE"),
                            255,
                        )

                        exame.situacao = normalizar_texto(
                            dados.get("SITUACAO"),
                            20,
                        )

                        exame.antibiograma = normalizar_texto(
                            dados.get("ANTIBIOGRAMA"),
                            20,
                        )

                        exame.exame_integrado_webservice = normalizar_texto(
                            dados.get("EXAME_INTEGRADO_WEBSERVICE"),
                            20,
                        )

                        exame.somente_solicitacao_pep = normalizar_texto(
                            dados.get("SOMENTE_SOLICITACAO_PEP"),
                            20,
                        )

                        exame.dados_spdata = dados

                    except Exception:
                        total_erros += 1

                        logger.exception(
                            "Erro processando exame SPDATA. Linha: %s",
                            total_lidos,
                        )

                try:
                    db.session.commit()

                    if on_progress:
                        on_progress({
                            "lidos": total_lidos,
                            "criados": total_criados,
                            "atualizados": total_atualizados,
                            "erros": total_erros,
                        })

                    logger.info(
                        "Lote concluído. Total processado: %s",
                        total_lidos,
                    )

                except Exception:
                    db.session.rollback()
                    logger.exception(
                        "Erro ao salvar lote de exames."
                    )
                    raise

        return {
            "lidos": total_lidos,
            "criados": total_criados,
            "atualizados": total_atualizados,
            "erros": total_erros,
        }

    except Exception:
        db.session.rollback()
        logger.exception("Falha na importação da SITABPRO.")
        raise
