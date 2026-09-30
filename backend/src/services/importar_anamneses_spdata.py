import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.model_mydsystem.med_spdata_anamneses_model import MedSpdataAnamnese
from src.modules.clinico.prontuario import (
    SPDATA_ANAMNESE_MODELO_COD,
    SPDATA_ANAMNESE_PERGUNTA_IDS,
    _montar_anamnese_spdata,
    _normalizar_sql_value,
)
from src.settings.extensions import db


logger = logging.getLogger(__name__)

# Recuo aplicado na carga padrão (incremental) para recapturar evoluções
# editadas no SPDATA depois de gravadas.
JANELA_RECUO_INCREMENTAL = timedelta(days=2)

COLUNAS_EVOLUCAO = (
    "ID_CABEVOL",
    "ID_HTATENDIMENTO",
    "ID_EVOLUCAO",
    "DATA_HORA_EVOLUCAO",
    "MODELO_COD",
    "MODELO_EVOLUCAO",
    "ID_PACIENTE_SPDATA",
    "PRONTUARIO",
    "PACIENTE",
)


def _texto(valor, limite=None):
    valor = _normalizar_sql_value(valor)
    if valor is None:
        return None
    valor = str(valor).strip()
    if limite:
        valor = valor[:limite]
    return valor or None


def _inteiro(valor):
    valor = _normalizar_sql_value(valor)
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _data_hora(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime.combine(valor, time.min)
    try:
        return datetime.fromisoformat(str(valor).strip())
    except ValueError:
        return None


def calcular_data_inicio(desde=None, completo=False):
    """Define a partir de quando importar.

    - `--completo`: tudo (None).
    - `--desde`: a data informada.
    - padrão: última evolução já espelhada menos a janela de recuo; se a
      tabela estiver vazia, importa tudo.
    """
    if completo:
        return None
    if desde is not None:
        return _data_hora(desde)

    ultima = db.session.execute(
        select(func.max(MedSpdataAnamnese.data_hora_evolucao))
    ).scalar()
    if ultima is None:
        return None
    return ultima - JANELA_RECUO_INCREMENTAL


def _sql_evolucoes(com_filtro_data):
    filtro_data = "AND PC.DATA_HORA_EVOLUCAO >= ?" if com_filtro_data else ""
    return f"""
        SELECT
            PC.ID_CABEVOL,
            PC.ID_HTATENDIMENTO,
            PC.ID_EVOLUCAO,
            PC.DATA_HORA_EVOLUCAO,
            PE.COD AS MODELO_COD,
            PE.DESCRICAO AS MODELO_EVOLUCAO,
            RP.ID AS ID_PACIENTE_SPDATA,
            RP.PRONT AS PRONTUARIO,
            RP.NOME AS PACIENTE
        FROM PRCABEVOL PC
        INNER JOIN PREVOLUCAO PE
            ON PE.ID_EVOLUCAO = PC.ID_EVOLUCAO
        INNER JOIN HTPACIENTE HP
            ON HP.ID = PC.ID_HTPACIENTE
        INNER JOIN RICADPAC RP
            ON RP.ID = HP.ID_RICADPAC
        WHERE PE.COD = ?
          {filtro_data}
        ORDER BY
            PC.DATA_HORA_EVOLUCAO,
            PC.ID_CABEVOL
    """


def _sql_respostas(quantidade_ids):
    placeholders = ", ".join("?" for _ in range(quantidade_ids))
    pergunta_ids_sql = ", ".join(str(int(id_pergunta)) for id_pergunta in SPDATA_ANAMNESE_PERGUNTA_IDS)
    return f"""
        SELECT
            PV.ID_CABEVOL,
            PP.ID AS ID_PERGUNTA,
            PP.DESCRICAO AS PERGUNTA,
            PV.CONTEVOL AS RESPOSTA
        FROM PREVOLPAC PV
        INNER JOIN PRRESPOSTA PR
            ON PR.ID_RESPOSTA = PV.ID_RESPOSTA
        INNER JOIN PRPERGUNTA PP
            ON PP.ID = PR.ID_PRPERGUNTA
        WHERE PV.ID_CABEVOL IN ({placeholders})
          AND PP.ID IN ({pergunta_ids_sql})
        ORDER BY
            PV.ID_CABEVOL,
            PP.ID
    """


def _buscar_respostas(cursor, ids_cabevol):
    """Retorna {id_cabevol: [ {ID_PERGUNTA, PERGUNTA, RESPOSTA}, ... ]}."""
    if not ids_cabevol:
        return {}

    cursor.execute(_sql_respostas(len(ids_cabevol)), list(ids_cabevol))
    respostas = {}
    for row in cursor.fetchall():
        id_cabevol = _inteiro(row[0])
        respostas.setdefault(id_cabevol, []).append({
            "ID_PERGUNTA": _inteiro(row[1]),
            "PERGUNTA": _normalizar_sql_value(row[2]),
            "RESPOSTA": _normalizar_sql_value(row[3]),
        })
    return respostas


def _aplicar_evolucao(registro, evolucao, respostas):
    registro.id_htatendimento = _inteiro(evolucao["ID_HTATENDIMENTO"])
    registro.id_evolucao = _inteiro(evolucao["ID_EVOLUCAO"])
    registro.modelo_cod = _texto(evolucao["MODELO_COD"], 20)
    registro.modelo_descricao = _texto(evolucao["MODELO_EVOLUCAO"], 255)
    registro.id_paciente_spdata = _inteiro(evolucao["ID_PACIENTE_SPDATA"])
    registro.prontuario = _texto(evolucao["PRONTUARIO"], 50)
    registro.paciente = _texto(evolucao["PACIENTE"], 255)
    registro.data_hora_evolucao = _data_hora(evolucao["DATA_HORA_EVOLUCAO"])
    registro.anamnese = _montar_anamnese_spdata(respostas)
    registro.dados_spdata = {"respostas": respostas}


def importar_anamneses_spdata(batch_size=200, desde=None, completo=False):
    total_lidos = 0
    total_criados = 0
    total_atualizados = 0
    total_erros = 0

    data_inicio = calcular_data_inicio(desde=desde, completo=completo)
    params = [SPDATA_ANAMNESE_MODELO_COD]
    if data_inicio is not None:
        params.append(data_inicio)

    logger.info(
        "Importação de anamneses SPDATA iniciada. modelo=%s desde=%s",
        SPDATA_ANAMNESE_MODELO_COD,
        data_inicio.isoformat() if data_inicio else "inicio",
    )

    try:
        with ConnectionDBFireBird() as connection:
            cursor_evolucoes = connection.cursor()
            cursor_respostas = connection.cursor()
            try:
                cursor_evolucoes.execute(_sql_evolucoes(data_inicio is not None), params)

                while True:
                    rows = cursor_evolucoes.fetchmany(batch_size)
                    if not rows:
                        break

                    evolucoes = [dict(zip(COLUNAS_EVOLUCAO, row)) for row in rows]
                    ids_cabevol = {
                        id_cabevol
                        for id_cabevol in (_inteiro(ev["ID_CABEVOL"]) for ev in evolucoes)
                        if id_cabevol is not None
                    }

                    respostas_por_cabevol = _buscar_respostas(cursor_respostas, ids_cabevol)

                    existentes = db.session.execute(
                        select(MedSpdataAnamnese).where(MedSpdataAnamnese.id_cabevol.in_(ids_cabevol))
                    ).scalars().all() if ids_cabevol else []
                    existentes_por_id = {registro.id_cabevol: registro for registro in existentes}

                    for evolucao in evolucoes:
                        total_lidos += 1
                        try:
                            id_cabevol = _inteiro(evolucao["ID_CABEVOL"])
                            if id_cabevol is None:
                                total_erros += 1
                                logger.warning(
                                    "Anamnese ignorada sem ID_CABEVOL. Linha: %s",
                                    total_lidos,
                                )
                                continue

                            registro = existentes_por_id.get(id_cabevol)
                            if registro is None:
                                registro = MedSpdataAnamnese(id_cabevol=id_cabevol)
                                db.session.add(registro)
                                existentes_por_id[id_cabevol] = registro
                                total_criados += 1
                            else:
                                total_atualizados += 1

                            _aplicar_evolucao(
                                registro,
                                evolucao,
                                respostas_por_cabevol.get(id_cabevol, []),
                            )
                        except Exception:
                            total_erros += 1
                            logger.exception(
                                "Erro processando anamnese do SPDATA. Linha: %s",
                                total_lidos,
                            )

                    db.session.commit()
            finally:
                cursor_respostas.close()
                cursor_evolucoes.close()

        resultado = {
            "desde": data_inicio,
            "lidos": total_lidos,
            "criados": total_criados,
            "atualizados": total_atualizados,
            "erros": total_erros,
        }
        logger.info(
            "Importação de anamneses SPDATA concluída. lidos=%s criados=%s atualizados=%s erros=%s",
            total_lidos,
            total_criados,
            total_atualizados,
            total_erros,
        )
        return resultado
    except Exception:
        db.session.rollback()
        logger.exception("Falha na importação das anamneses do SPDATA.")
        raise
