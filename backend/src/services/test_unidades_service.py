from types import SimpleNamespace

import pytest

from src.services.unidades_service import resolver_unidade_usuario
from src.settings.extensions import db


class QueryMultiUnidade:
    def join(self, *_args, **_kwargs):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return [
            SimpleNamespace(unidade=SimpleNamespace(id=1, nome="Unidade A")),
            SimpleNamespace(unidade=SimpleNamespace(id=2, nome="Unidade B")),
        ]


class QueryUnidadeSelecionada(QueryMultiUnidade):
    def first(self):
        return SimpleNamespace(unidade=SimpleNamespace(id=2, nome="Unidade B"))


class ResultadoUnidadeAtiva:
    def __init__(self, unidade):
        self._unidade = unidade

    def scalar_one_or_none(self):
        return self._unidade


def _usuario_nao_admin(monkeypatch):
    monkeypatch.setattr(
        db.session,
        "get",
        lambda _model, _id: SimpleNamespace(role="recepcao"),
    )


def test_resolver_unidade_usuario_exige_unidade_ativa_para_multiunidade(monkeypatch):
    _usuario_nao_admin(monkeypatch)
    monkeypatch.setattr(db.session, "query", lambda _model: QueryMultiUnidade())

    with pytest.raises(PermissionError, match="Unidade ativa obrigatória"):
        resolver_unidade_usuario(10)


def test_resolver_unidade_usuario_aceita_unidade_informada_para_multiunidade(monkeypatch):
    _usuario_nao_admin(monkeypatch)
    monkeypatch.setattr(db.session, "query", lambda _model: QueryUnidadeSelecionada())

    unidade = resolver_unidade_usuario(10, unidade_id=2)

    assert unidade.id == 2


def test_resolver_unidade_usuario_admin_exige_unidade_informada(monkeypatch):
    monkeypatch.setattr(
        db.session,
        "get",
        lambda _model, _id: SimpleNamespace(role="admin"),
    )

    with pytest.raises(PermissionError, match="Unidade ativa obrigatória"):
        resolver_unidade_usuario(1)


def test_resolver_unidade_usuario_admin_aceita_unidade_ativa_sem_vinculo(monkeypatch):
    monkeypatch.setattr(
        db.session,
        "get",
        lambda _model, _id: SimpleNamespace(role="admin"),
    )
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda _consulta: ResultadoUnidadeAtiva(SimpleNamespace(id=3, nome="Unidade C")),
    )

    unidade = resolver_unidade_usuario(1, unidade_id=3)

    assert unidade.id == 3


def test_resolver_unidade_usuario_admin_rejeita_unidade_invalida(monkeypatch):
    monkeypatch.setattr(
        db.session,
        "get",
        lambda _model, _id: SimpleNamespace(role="admin"),
    )
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda _consulta: ResultadoUnidadeAtiva(None),
    )

    with pytest.raises(PermissionError, match="não possui acesso à unidade informada"):
        resolver_unidade_usuario(1, unidade_id=99)
