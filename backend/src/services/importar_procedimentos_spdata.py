import logging

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import select

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.model_mydsystem.med_procedimentos_model import Procedimento
from src.settings.extensions import db


logger = logging.getLogger(__name__)


def normalizar_valor(valor):
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        if valor == valor.to_integral_value():
            return int(valor)
        return float(valor)
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.hex()
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


def normalizar_int(valor):
    if valor is None or valor == "":
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        try:
            return int(float(str(valor).replace(",", ".")))
        except (TypeError, ValueError):
            return None


def normalizar_float(valor):
    if valor is None or valor == "":
        return None

    try:
        return float(valor)
    except (TypeError, ValueError):
        try:
            return float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            return None


def row_para_dict(row, nomes_colunas):
    return {
        nome: normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def procedimento_ativo(dados):
    situacao = normalizar_texto(dados.get("TM_SITUACAO"), 10)
    centro_situacao = normalizar_texto(dados.get("TH_SITUACAO"), 10)
    bloqueio = normalizar_texto(dados.get("BLOQUEIO"), 10)

    return situacao == "A" and centro_situacao == "A" and bloqueio not in {"T", "S", "1"}


def importar_procedimentos_spdata(batch_size=200):
    total_lidos = 0
    total_criados = 0
    total_atualizados = 0
    total_erros = 0

    sql = """
        SELECT
            TP.ID AS TP_ID,
            TP.ID_TBCTRTHM,
            TP.COD_PROCEDIMENTO,
            TP.NOME AS TP_NOME,
            TP.TP_MODULO,
            TH.COD AS TH_COD,
            TH.NOME AS TH_NOME,
            TH.SITUACAO AS TH_SITUACAO,
            TM.ID_TBPROCTO,
            TM.TAB,
            TM.COD AS TM_COD,
            TM.NOME AS TM_NOME,
            TM.TIPOATO,
            TA.NOME AS TIPOATO_NOME,
            TM.CH,
            TM.AUX,
            TM.FILME,
            TM.COPE,
            TM.PROCMED,
            TM.STAND,
            TM.PACOTE,
            TM.SITUACAO AS TM_SITUACAO,
            TM.TAB_REF,
            TM.PROC_REF,
            TM.TAB_REF_TUSS,
            TM.PROC_REF_TUSS,
            TM.EXIGE_AUTORIZACAO,
            TM.QTDE_MAX_GUIA,
            TM.APELIDO_PROCEDIMENTO,
            TM.BLOQUEIO
        FROM TBPROCTO TP
        JOIN TBCTRTHM TH ON TH.COD = TP.ID_TBCTRTHM
        JOIN TBTABTHM TM
          ON TM.ID_TBPROCTO = TP.ID
         AND TM.COD = TP.COD_PROCEDIMENTO
        LEFT JOIN TBTABATO TA ON TA.COD = TM.TIPOATO
        WHERE TM.TAB = ?
        ORDER BY TM.NOME
    """

    try:
        with ConnectionDBFireBird() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, (98,))
            nomes_colunas = [descricao[0].strip().upper() for descricao in cursor.description]

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break

                chaves = []
                for row in rows:
                    dados = row_para_dict(row, nomes_colunas)
                    tab = normalizar_int(dados.get("TAB"))
                    codigo = normalizar_int(dados.get("COD_PROCEDIMENTO") or dados.get("TM_COD"))
                    if tab is not None and codigo is not None:
                        chaves.append((tab, codigo))

                existentes = []
                if chaves:
                    tabs = {tab for tab, _codigo in chaves}
                    codigos = {codigo for _tab, codigo in chaves}
                    existentes = db.session.execute(
                        select(Procedimento).where(
                            Procedimento.tab.in_(tabs),
                            Procedimento.codigo_procedimento.in_(codigos),
                        )
                    ).scalars().all()

                existentes_por_chave = {
                    (procedimento.tab, procedimento.codigo_procedimento): procedimento
                    for procedimento in existentes
                }

                for row in rows:
                    total_lidos += 1

                    try:
                        dados = row_para_dict(row, nomes_colunas)
                        tab = normalizar_int(dados.get("TAB"))
                        codigo = normalizar_int(dados.get("COD_PROCEDIMENTO") or dados.get("TM_COD"))
                        spdata_tp_id = normalizar_int(dados.get("TP_ID") or dados.get("ID_TBPROCTO"))
                        id_tbctrthm = normalizar_int(dados.get("ID_TBCTRTHM") or dados.get("TH_COD"))

                        if tab is None or codigo is None or spdata_tp_id is None or id_tbctrthm is None:
                            total_erros += 1
                            logger.warning(
                                "Procedimento ignorado por chave incompleta. Linha: %s",
                                total_lidos,
                            )
                            continue

                        nome = normalizar_texto(dados.get("TM_NOME") or dados.get("TP_NOME"), 255)
                        if not nome:
                            nome = f"Procedimento SPDATA {codigo}"

                        chave = (tab, codigo)
                        procedimento = existentes_por_chave.get(chave)
                        if procedimento is None:
                            procedimento = Procedimento(
                                tab=tab,
                                codigo_procedimento=codigo,
                                spdata_tp_id=spdata_tp_id,
                                id_tbctrthm=id_tbctrthm,
                            )
                            db.session.add(procedimento)
                            existentes_por_chave[chave] = procedimento
                            total_criados += 1
                        else:
                            total_atualizados += 1

                        procedimento.spdata_tp_id = spdata_tp_id
                        procedimento.id_tbctrthm = id_tbctrthm
                        procedimento.nome = nome
                        procedimento.apelido_procedimento = normalizar_texto(
                            dados.get("APELIDO_PROCEDIMENTO"),
                            100,
                        )
                        procedimento.tipo_modulo = normalizar_texto(dados.get("TP_MODULO"), 10)
                        procedimento.tipo_ato_codigo = normalizar_int(dados.get("TIPOATO"))
                        procedimento.tipo_ato_nome = normalizar_texto(dados.get("TIPOATO_NOME"), 100)
                        procedimento.centro_tabela_nome = normalizar_texto(dados.get("TH_NOME"), 100)
                        procedimento.centro_tabela_situacao = normalizar_texto(dados.get("TH_SITUACAO"), 10)
                        procedimento.situacao = normalizar_texto(dados.get("TM_SITUACAO"), 10)
                        procedimento.ativo = procedimento_ativo(dados)
                        procedimento.ch = normalizar_float(dados.get("CH"))
                        procedimento.aux = normalizar_int(dados.get("AUX"))
                        procedimento.filme = normalizar_float(dados.get("FILME"))
                        procedimento.cope = normalizar_float(dados.get("COPE"))
                        procedimento.procmed = normalizar_texto(dados.get("PROCMED"), 10)
                        procedimento.stand = normalizar_texto(dados.get("STAND"), 10)
                        procedimento.pacote = normalizar_texto(dados.get("PACOTE"), 10)
                        procedimento.tab_ref = normalizar_int(dados.get("TAB_REF"))
                        procedimento.proc_ref = normalizar_int(dados.get("PROC_REF"))
                        procedimento.tab_ref_tuss = normalizar_int(dados.get("TAB_REF_TUSS"))
                        procedimento.proc_ref_tuss = normalizar_int(dados.get("PROC_REF_TUSS"))
                        procedimento.exige_autorizacao = normalizar_int(dados.get("EXIGE_AUTORIZACAO"))
                        procedimento.qtde_max_guia = normalizar_int(dados.get("QTDE_MAX_GUIA"))
                        procedimento.bloqueio = normalizar_texto(dados.get("BLOQUEIO"), 10)
                        procedimento.dados_spdata = dados

                    except Exception:
                        total_erros += 1
                        logger.exception(
                            "Erro processando procedimento SPDATA. Linha: %s",
                            total_lidos,
                        )

                try:
                    db.session.commit()
                    logger.info(
                        "Lote de procedimentos concluído. Total processado: %s",
                        total_lidos,
                    )
                except Exception:
                    db.session.rollback()
                    logger.exception("Erro ao salvar lote de procedimentos.")
                    raise

        return {
            "lidos": total_lidos,
            "criados": total_criados,
            "atualizados": total_atualizados,
            "erros": total_erros,
        }

    except Exception:
        db.session.rollback()
        logger.exception("Falha na importação dos procedimentos do SPDATA.")
        raise
