from types import SimpleNamespace

from src.modules.exames.service import exame_para_dict, filtro_busca_exames


def test_exame_para_dict_retorna_catalogo_basico():
    exame = SimpleNamespace(
        id=1,
        nome="Hemograma",
        codigo_alfanumerico="HEMO",
        codigo_amb="40304361",
    )

    assert exame_para_dict(exame) == {
        "id": 1,
        "nome": "Hemograma",
        "codigo_alfanumerico": "HEMO",
        "codigo_amb": "40304361",
    }


def test_filtro_busca_exames_considera_codigos():
    filtro = filtro_busca_exames("40304361")
    sql = str(filtro.compile(compile_kwargs={"literal_binds": True}))

    assert "codigo_alfanumerico" in sql
    assert "codigo_amb" in sql
    assert "40304361" in sql
