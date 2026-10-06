from types import SimpleNamespace

from src.services.spdata_atendimentos_service import (
    aplicar_cid_personalizado,
    normalizar_cid_personalizado,
)


def test_normalizar_cid_personalizado_normaliza_codigo_e_descricao():
    resultado = normalizar_cid_personalizado({
        "cid": " j06.9 ",
        "descricao": " Infecção aguda ",
    })

    assert resultado == {
        "codigo": "J06.9",
        "descricao": "Infecção aguda",
    }


def test_normalizar_cid_personalizado_aceita_nomes_alternativos():
    resultado = normalizar_cid_personalizado({
        "codigo": "r50.9",
        "nome": "Febre",
    })

    assert resultado == {"codigo": "R50.9", "descricao": "Febre"}


def test_normalizar_cid_personalizado_rejeita_valores_sem_codigo():
    assert normalizar_cid_personalizado(None) is None
    assert normalizar_cid_personalizado("J06.9") is None
    assert normalizar_cid_personalizado({"descricao": "Sem código"}) is None


def test_aplicar_cid_personalizado_persiste_e_limpa_valores():
    atendimento = SimpleNamespace(
        cid_personalizado=None,
        cid_personalizado_descricao=None,
    )

    aplicar_cid_personalizado(atendimento, {
        "cid_personalizado": {"cid": "j06.9", "descricao": "Infecção aguda"},
    })
    assert atendimento.cid_personalizado == "J06.9"
    assert atendimento.cid_personalizado_descricao == "Infecção aguda"

    aplicar_cid_personalizado(atendimento, {"cid_personalizado": None})
    assert atendimento.cid_personalizado is None
    assert atendimento.cid_personalizado_descricao is None


def test_aplicar_cid_personalizado_preserva_valor_quando_campo_esta_ausente():
    atendimento = SimpleNamespace(
        cid_personalizado="R50.9",
        cid_personalizado_descricao="Febre",
    )

    aplicar_cid_personalizado(atendimento, {})

    assert atendimento.cid_personalizado == "R50.9"
    assert atendimento.cid_personalizado_descricao == "Febre"
