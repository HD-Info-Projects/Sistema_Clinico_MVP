import logging
from datetime import date, datetime, time

import pyodbc

from src.models.db.handler_sql_server import ConnectionSqlServer

logger = logging.getLogger(__name__)


class BioDataUnavailableError(RuntimeError):
    """Raised when the external BioData SQL Server cannot be reached."""


def _normalizar_sql_value(valor):
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()

    if hasattr(valor, "read"):
        return _normalizar_sql_value(valor.read())

    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.decode("cp1252", errors="replace")

    return valor


def executar_historico_biodata(where_clause, params, limit, offset):
    row_start = offset + 1
    row_end = offset + limit + 1
    sql = f"""
        WITH historico AS (
            SELECT
                an.intAnamneseId AS ID_ANAMNESE,
                an.datAnamnese AS DATA_ANAMNESE,
                CAST(an.strAnamnese AS NVARCHAR(MAX)) AS ANAMNESE_RTF,
                CAST(an.strAnamneseMobile AS NVARCHAR(MAX)) AS ANAMNESE_MOBILE,
                c.intClienteId AS ID_PACIENTE_BIODATA,
                c.strCliente AS PACIENTE,
                c.strCPF AS CPF,
                p.strProfissional AS MEDICO,
                ROW_NUMBER() OVER (
                    ORDER BY an.datAnamnese DESC, an.intAnamneseId DESC
                ) AS RN
            FROM [BioData].[dbo].[tblAnamnese] an
            JOIN [Repositorio].[dbo].[tblCliente] c
                ON c.intClienteId = an.intClienteId
            LEFT JOIN [BioData].[dbo].[tblProfissional] p
                ON p.intProfissionalId = an.intProfissionalId
            WHERE {where_clause}
        )
        SELECT
            ID_ANAMNESE,
            DATA_ANAMNESE,
            ANAMNESE_RTF,
            ANAMNESE_MOBILE,
            ID_PACIENTE_BIODATA,
            PACIENTE,
            CPF,
            MEDICO
        FROM historico
        WHERE RN BETWEEN ? AND ?
        ORDER BY RN;
    """

    try:
        with ConnectionSqlServer() as con:
            cursor = con.cursor()
            cursor.execute(sql, [*params, row_start, row_end])
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
    except pyodbc.Error as exc:
        logger.warning("BioData indisponivel ao consultar historico", exc_info=True)
        raise BioDataUnavailableError("BioData indisponível") from exc

    items = [
        {
            coluna: _normalizar_sql_value(valor)
            for coluna, valor in zip(columns, row)
        }
        for row in rows
    ]
    return items[:limit], len(items) > limit


def buscar_historico_biodata(cpf, nome, limit, offset):
    historico = []
    has_more = False

    if cpf:
        historico, has_more = executar_historico_biodata(
            "c.strCPF = ?",
            [cpf],
            limit,
            offset,
        )

    if not historico and nome and (not cpf or offset == 0):
        historico, has_more = executar_historico_biodata(
            "UPPER(LTRIM(RTRIM(c.strCliente))) = UPPER(LTRIM(RTRIM(?)))",
            [nome],
            limit,
            offset,
        )

    return historico, has_more


__all__ = [
    "BioDataUnavailableError",
    "ConnectionSqlServer",
    "buscar_historico_biodata",
    "executar_historico_biodata",
]
