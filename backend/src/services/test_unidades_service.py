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


def test_resolver_unidade_usuario_exige_unidade_ativa_para_multiunidade(monkeypatch):
    monkeypatch.setattr(db.session, "query", lambda _model: QueryMultiUnidade())

    with pytest.raises(PermissionError, match="Unidade ativa obrigatória"):
        resolver_unidade_usuario(10)


def test_resolver_unidade_usuario_aceita_unidade_informada_para_multiunidade(monkeypatch):
    monkeypatch.setattr(db.session, "query", lambda _model: QueryUnidadeSelecionada())

    unidade = resolver_unidade_usuario(10, unidade_id=2)

    assert unidade.id == 2
