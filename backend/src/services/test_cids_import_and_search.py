import importlib

import pytest
from flask import Flask

from src.models.model_mydsystem.med_spdata_cids_model import MedSpdataCid
from src.services.cids_service import buscar_cids_locais
from src.settings.extensions import db


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


class FakeCursor:
    def __init__(self, batches):
        self.batches = list(batches)
        self.sql = None

    def execute(self, sql):
        self.sql = sql

    def fetchmany(self, _batch_size):
        if not self.batches:
            return []
        return self.batches.pop(0)


class FakeConnection:
    def __init__(self, batches):
        self.cursor_instance = FakeCursor(batches)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_instance


def fake_firebird(monkeypatch, batches):
    service_module = importlib.import_module("src.services.importar_cids_spdata")
    monkeypatch.setattr(
        service_module,
        "ConnectionDBFireBird",
        lambda: FakeConnection(batches),
    )
    return service_module


def test_importar_cids_spdata_cria_atualiza_e_preserva(monkeypatch, app_context):
    service_module = fake_firebird(
        monkeypatch,
        [[(" a00 ", "Colera"), ("B20", "Doenca pelo HIV")]],
    )

    resultado = service_module.importar_cids_spdata(batch_size=1)

    assert resultado == {
        "lidos": 2,
        "criados": 2,
        "atualizados": 0,
        "inalterados": 0,
        "duplicados": 0,
        "erros": 0,
    }
    assert MedSpdataCid.query.count() == 2
    assert MedSpdataCid.query.filter_by(codigo="A00").one().nome == "Colera"

    service_module = fake_firebird(monkeypatch, [[("A00", "Colera atualizada")]])

    resultado = service_module.importar_cids_spdata(batch_size=1)

    assert resultado["criados"] == 0
    assert resultado["atualizados"] == 1
    assert MedSpdataCid.query.count() == 2
    assert MedSpdataCid.query.filter_by(codigo="A00").one().nome == "Colera atualizada"
    assert MedSpdataCid.query.filter_by(codigo="B20").one().nome == "Doenca pelo HIV"


def test_importar_cids_spdata_faz_rollback_em_falha(monkeypatch, app_context):
    db.session.add(MedSpdataCid(codigo="Z99", nome="Descricao antiga"))
    db.session.commit()

    service_module = fake_firebird(
        monkeypatch,
        [[("Z99", "Descricao nova")], [("A00", "Colera"), ("A00", "Conflito")]],
    )

    with pytest.raises(ValueError):
        service_module.importar_cids_spdata(batch_size=1)

    assert MedSpdataCid.query.count() == 1
    assert MedSpdataCid.query.filter_by(codigo="Z99").one().nome == "Descricao antiga"


def test_importar_cids_spdata_ignora_linhas_invalidas(monkeypatch, app_context):
    service_module = fake_firebird(
        monkeypatch,
        [[(None, "Sem codigo"), ("   ", "Codigo vazio"), ("B20", "")], [("A00", "Colera")]],
    )

    resultado = service_module.importar_cids_spdata(batch_size=3)

    assert resultado == {
        "lidos": 4,
        "criados": 1,
        "atualizados": 0,
        "inalterados": 0,
        "duplicados": 0,
        "erros": 3,
    }
    assert MedSpdataCid.query.count() == 1
    assert MedSpdataCid.query.filter_by(codigo="A00").one().nome == "Colera"


def test_importar_cids_spdata_conta_duplicados_identicos(monkeypatch, app_context):
    service_module = fake_firebird(
        monkeypatch,
        [[("A00", "Colera")], [("A00", "Colera"), ("B20", "Doenca pelo HIV")]],
    )

    resultado = service_module.importar_cids_spdata(batch_size=1)

    assert resultado == {
        "lidos": 3,
        "criados": 2,
        "atualizados": 0,
        "inalterados": 0,
        "duplicados": 1,
        "erros": 0,
    }
    assert MedSpdataCid.query.count() == 2


def test_importar_cids_spdata_falha_quando_nao_tem_cid_valido(monkeypatch, app_context):
    service_module = fake_firebird(monkeypatch, [[(None, "Sem codigo"), ("B20", "")]])

    with pytest.raises(RuntimeError):
        service_module.importar_cids_spdata(batch_size=10)

    assert MedSpdataCid.query.count() == 0


def test_buscar_cids_locais_filtra_pagina_e_escapa_like(app_context):
    db.session.add_all([
        MedSpdataCid(codigo="A00", nome="Colera"),
        MedSpdataCid(codigo="A01", nome="Febre tifoide"),
        MedSpdataCid(codigo="B20", nome="Doenca pelo HIV"),
        MedSpdataCid(codigo="C10", nome="Nome com 100% literal"),
        MedSpdataCid(codigo="C11", nome="Nome com 100X literal"),
    ])
    db.session.commit()

    por_codigo = buscar_cids_locais("A", limit=1, offset=0, is_codigo_cid=True)
    por_nome = buscar_cids_locais("hiv", limit=20, offset=0, is_codigo_cid=False)
    por_literal = buscar_cids_locais("100%", limit=20, offset=0, is_codigo_cid=False)

    assert por_codigo["items"] == [{"CID": "A00", "DOENCA": "Colera"}]
    assert por_codigo["has_more"] is True
    assert por_nome["items"] == [{"CID": "B20", "DOENCA": "Doenca pelo HIV"}]
    assert por_literal["items"] == [{"CID": "C10", "DOENCA": "Nome com 100% literal"}]
