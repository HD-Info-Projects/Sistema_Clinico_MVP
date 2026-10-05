from types import SimpleNamespace

from src.modules.procedimentos.service import filtro_busca_procedimentos, procedimento_para_dict


def test_procedimento_para_dict_retorna_codigo_procedimento():
    procedimento = SimpleNamespace(
        id=1,
        nome="Acuidade Visual",
        codigo_procedimento=1307,
        tipo_ato_codigo=None,
        tipo_ato_nome=None,
        apelido_procedimento=None,
        exige_autorizacao=None,
        qtde_max_guia=None,
    )

    resultado = procedimento_para_dict(procedimento)

    assert resultado["codigo_procedimento"] == 1307
    assert "codigo_tuss" not in resultado


def test_filtro_busca_procedimentos_considera_codigo_procedimento_e_nao_tuss():
    filtro = filtro_busca_procedimentos("1307")
    sql = str(filtro.compile(compile_kwargs={"literal_binds": True}))

    assert "codigo_procedimento" in sql
    assert "proc_ref_tuss" not in sql
    assert "1307" in sql
