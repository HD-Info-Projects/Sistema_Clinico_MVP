from types import SimpleNamespace

from src.routes.procedimentos_route import filtro_busca_procedimentos, procedimento_para_dict


def test_procedimento_para_dict_retorna_codigo_tuss():
    procedimento = SimpleNamespace(
        id=1,
        nome="Acuidade Visual",
        codigo_procedimento=1307,
        proc_ref_tuss=41301307,
        tipo_ato_codigo=None,
        tipo_ato_nome=None,
        apelido_procedimento=None,
        exige_autorizacao=None,
        qtde_max_guia=None,
    )

    assert procedimento_para_dict(procedimento)["codigo_tuss"] == 41301307


def test_filtro_busca_procedimentos_considera_codigo_tuss():
    filtro = filtro_busca_procedimentos("41301471")
    sql = str(filtro.compile(compile_kwargs={"literal_binds": True}))

    assert "proc_ref_tuss" in sql
    assert "41301471" in sql
