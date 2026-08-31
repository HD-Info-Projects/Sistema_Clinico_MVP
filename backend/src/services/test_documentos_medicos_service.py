from src.services.documentos_medicos_service import (
    descricao_procedimentos,
    normalizar_procedimentos_documento,
)


def test_descricao_procedimentos_prefere_codigo_tuss():
    descricao = descricao_procedimentos([
        {
            "nome": "Acuidade Visual",
            "codigo_procedimento": 1307,
            "codigo_tuss": 41301307,
        }
    ])

    assert descricao == "41301307 - Acuidade Visual"


def test_normalizar_procedimentos_preserva_codigo_tuss_sem_catalogo():
    procedimentos = normalizar_procedimentos_documento([
        {
            "nome": "Teste do Olhinho | teste do reflexo vermelho",
            "codigo_procedimento": 1471,
            "codigo_tuss": 41301471,
        }
    ])

    assert procedimentos[0]["codigo_tuss"] == 41301471
