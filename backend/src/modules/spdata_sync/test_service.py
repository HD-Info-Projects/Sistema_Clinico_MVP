from types import SimpleNamespace

import pytest

from src.integrations.spdata import catalog_sync as service


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "TODOS"),
        ("todos", "TODOS"),
        (" exames ", "EXAMES"),
        ("procedimentos", "PROCEDIMENTOS"),
    ],
)
def test_normalizar_target(value, expected):
    assert service._normalizar_target(value) == expected


def test_normalizar_target_rejeita_catalogo_desconhecido():
    with pytest.raises(service.InvalidTargetError):
        service._normalizar_target("pacientes")


def test_stages_respeita_catalogo_solicitado():
    assert service._stages("EXAMES") == ("EXAMES",)
    assert service._stages("PROCEDIMENTOS") == ("PROCEDIMENTOS",)
    assert service._stages("TODOS") == ("EXAMES", "PROCEDIMENTOS")


def test_atualizar_progresso_preserva_outra_etapa(monkeypatch):
    job = SimpleNamespace(
        progress={"exames": {"lidos": 20}},
        heartbeat_at=None,
    )
    commits = []
    monkeypatch.setattr(service.db.session, "get", lambda *_args: job)
    monkeypatch.setattr(service.db.session, "commit", lambda: commits.append(True))

    service._atualizar_progresso(
        10,
        "PROCEDIMENTOS",
        {"lidos": 5, "criados": 1, "atualizados": 4, "erros": 0},
    )

    assert job.progress["exames"] == {"lidos": 20}
    assert job.progress["procedimentos"]["lidos"] == 5
    assert job.heartbeat_at is not None
    assert commits == [True]
