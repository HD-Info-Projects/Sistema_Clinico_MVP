from datetime import datetime

import pytest

from src import create_app
from src.models.model_mydsystem.med_spdata_anamneses_model import MedSpdataAnamnese
from src.services import importar_anamneses_spdata as service
from src.settings.config import Config
from src.settings.extensions import db


EVOLUCOES = [
    # ID_CABEVOL, ID_HTATENDIMENTO, ID_EVOLUCAO, DATA_HORA, MODELO_COD, MODELO, ID_PAC, PRONT, PACIENTE
    (10, 500, 26, datetime(2026, 9, 1, 8, 0), "MED26", "Anamnese médica", 1, "P001", "Paciente A"),
    (11, 501, 26, datetime(2026, 9, 20, 9, 30), "MED26", "Anamnese médica", 2, "P002", "Paciente B"),
]

RESPOSTAS = [
    (10, 2171, "Queixa principal", "Dor de cabeça"),
    (10, 2172, "HDA", r"{\rtf1\ansi Inicio ha 2 dias\par}"),
    (11, 2171, "Queixa principal", "Febre"),
]


class CursorFake:
    def __init__(self, registro):
        self.registro = registro
        self.linhas = []

    def execute(self, sql, params=None):
        params = list(params or [])
        self.registro.append((sql, params))
        if "FROM PRCABEVOL" in sql:
            linhas = [row for row in self.registro.evolucoes if row[4] == params[0]]
            if len(params) > 1:
                linhas = [row for row in linhas if row[3] >= params[1]]
            self.linhas = linhas
        else:
            ids = set(params)
            self.linhas = [row for row in self.registro.respostas if row[0] in ids]

    def fetchmany(self, size):
        lote, self.linhas = self.linhas[:size], self.linhas[size:]
        return lote

    def fetchall(self):
        lote, self.linhas = self.linhas, []
        return lote

    def close(self):
        pass


class RegistroSql(list):
    def __init__(self, evolucoes, respostas):
        super().__init__()
        self.evolucoes = evolucoes
        self.respostas = respostas


class ConexaoFake:
    def __init__(self, registro):
        self.registro = registro

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def cursor(self):
        return CursorFake(self.registro)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    app = create_app()

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def firebird(monkeypatch):
    registro = RegistroSql(list(EVOLUCOES), list(RESPOSTAS))
    monkeypatch.setattr(service, "ConnectionDBFireBird", lambda: ConexaoFake(registro))
    return registro


def test_importa_evolucoes_e_monta_anamnese(app, firebird):
    resultado = service.importar_anamneses_spdata(batch_size=1)

    assert resultado["lidos"] == 2
    assert resultado["criados"] == 2
    assert resultado["atualizados"] == 0
    assert resultado["erros"] == 0
    assert resultado["desde"] is None

    registro = db.session.query(MedSpdataAnamnese).filter_by(id_cabevol=10).one()
    assert registro.prontuario == "P001"
    assert registro.id_paciente_spdata == 1
    assert registro.data_hora_evolucao == datetime(2026, 9, 1, 8, 0)
    assert "Queixa principal: Dor de cabeça" in registro.anamnese
    assert "HDA: Inicio ha 2 dias" in registro.anamnese
    assert len(registro.dados_spdata["respostas"]) == 2


def test_segunda_execucao_nao_duplica(app, firebird):
    service.importar_anamneses_spdata(completo=True)
    resultado = service.importar_anamneses_spdata(completo=True)

    assert resultado["criados"] == 0
    assert resultado["atualizados"] == 2
    assert db.session.query(MedSpdataAnamnese).count() == 2


def test_carga_padrao_continua_da_ultima_evolucao_com_recuo(app, firebird):
    service.importar_anamneses_spdata()

    firebird.evolucoes.append(
        (12, 502, 26, datetime(2026, 9, 25, 10, 0), "MED26", "Anamnese médica", 3, "P003", "Paciente C")
    )
    resultado = service.importar_anamneses_spdata()

    assert resultado["desde"] == datetime(2026, 9, 18, 9, 30)
    assert resultado["lidos"] == 2  # evolução 11 (dentro do recuo) + nova 12
    assert resultado["criados"] == 1
    assert resultado["atualizados"] == 1
    assert db.session.query(MedSpdataAnamnese).count() == 3


def test_desde_filtra_por_data(app, firebird):
    resultado = service.importar_anamneses_spdata(desde=datetime(2026, 9, 10))

    assert resultado["lidos"] == 1
    assert db.session.query(MedSpdataAnamnese).one().id_cabevol == 11
    sql_evolucoes, params = firebird[0]
    assert "PC.DATA_HORA_EVOLUCAO >= ?" in sql_evolucoes
    assert params == ["MED26", datetime(2026, 9, 10)]


def test_consulta_respostas_restringe_perguntas_do_prontuario(app, firebird):
    service.importar_anamneses_spdata()

    sql_respostas = next(sql for sql, _ in firebird if "FROM PREVOLPAC" in sql)
    assert "PP.ID IN (2171, 2172, 2173, 2174, 2176, 2780)" in sql_respostas


def test_comando_cli_exibe_resumo(app, firebird):
    resultado = app.test_cli_runner().invoke(args=["importar-anamneses-spdata"])

    assert resultado.exit_code == 0, resultado.output
    assert "Lidos: 2" in resultado.output
    assert "Criados: 2" in resultado.output


def test_comando_cli_rejeita_desde_com_completo(app, firebird):
    resultado = app.test_cli_runner().invoke(
        args=["importar-anamneses-spdata", "--desde", "2026-09-01", "--completo"]
    )

    assert resultado.exit_code != 0
    assert "Use --desde ou --completo" in resultado.output
