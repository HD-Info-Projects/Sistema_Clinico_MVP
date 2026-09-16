"""BioData SQL Server integration facade."""

from src.models.db.handler_sql_server import ConnectionSqlServer
from src.routes.prontuario_route import (
    _executar_historico_biodata as executar_historico_biodata,
    _historico_biodata as historico_biodata,
)

__all__ = [
    "ConnectionSqlServer",
    "executar_historico_biodata",
    "historico_biodata",
]
