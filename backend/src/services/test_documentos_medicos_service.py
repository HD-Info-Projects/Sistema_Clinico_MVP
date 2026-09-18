from types import SimpleNamespace

from src.services.documentos_medicos_service import (
    cids_atendimento_para_documento,
    descricao_procedimentos,
    normalizar_procedimentos_documento,
    validar_dados_documento,
)
from src.models.documento_medico_model import TIPO_ATESTADO


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


def test_cids_atendimento_para_documento_prioriza_principal_e_limita_quatro_codigos():
    atendimento = SimpleNamespace(diagnosticos=[
        SimpleNamespace(cid_codigo="R50.9", principal=False, created_at=None),
        SimpleNamespace(cid_codigo="J06.9", principal=True, created_at=None),
        SimpleNamespace(cid_codigo="E11.9", principal=False, created_at=None),
        SimpleNamespace(cid_codigo="I10", principal=False, created_at=None),
        SimpleNamespace(cid_codigo="Z00.0", principal=False, created_at=None),
        SimpleNamespace(cid_codigo="J06.9", principal=False, created_at=None),
    ])

    assert cids_atendimento_para_documento(atendimento) == [
        "J06.9",
        "R50.9",
        "E11.9",
        "I10",
    ]


def test_validar_atestado_persiste_apenas_codigos_cid():
    dados = validar_dados_documento(TIPO_ATESTADO, {
        "data_inicio": "2026-09-18",
        "dias_afastamento": 1,
        "cids": [
            {"cid": "J06.9", "nome": "Infecção aguda"},
            {"cid": "R50.9", "nome": "Febre"},
        ],
    })

    assert dados["cids"] == ["J06.9", "R50.9"]
