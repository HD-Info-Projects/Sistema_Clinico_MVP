import importlib.util
from pathlib import Path


def _load_route_module():
    path = Path(__file__).resolve().parent / "src/routes/spdata_exames_pacs_route.py"
    spec = importlib.util.spec_from_file_location("spdata_exames_pacs_route", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "message": "https://exemplo.com/imagem",
            "treatmentId": "823525",
        }


def test_chamar_viewer_exame_envia_treatment_id_823525(monkeypatch):
    route_module = _load_route_module()
    chamadas = []
    monkeypatch.setenv("URL_EXAMES_PACS", "https://pacs.exemplo.com/viewer")
    monkeypatch.setenv("TOKEN_EXAMES_PACS", "token-teste")

    def post_fake(url, headers=None, json=None, timeout=None):
        chamadas.append({
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
        })
        return FakeResponse()

    monkeypatch.setattr(route_module.requests, "post", post_fake)

    payload, status_code = route_module._chamar_viewer_exame(823525)

    assert status_code == 200
    assert payload == {
        "message": "https://exemplo.com/imagem",
        "treatmentId": "823525",
    }
    assert chamadas == [{
        "url": "https://pacs.exemplo.com/viewer",
        "headers": {
            "Authorization": "Bearer token-teste",
            "Content-Type": "application/json",
        },
        "json": {"treatmentId": "823525"},
        "timeout": 15,
    }]


def test_chamar_viewer_exame_reescreve_host_viewer_publico(monkeypatch):
    route_module = _load_route_module()
    monkeypatch.setenv("URL_EXAMES_PACS", "https://pacs.exemplo.com/viewer")
    monkeypatch.setenv("TOKEN_EXAMES_PACS", "token-teste")

    class FakeViewerResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "message": (
                    "https://192.168.5.21/viewer/viewer/"
                    "1.2.410.200001.101.11.302.1100234043.1.20251107073919690"
                    "?aet=SP1972&token="
                ),
                "treatmentId": "823525",
            }

    monkeypatch.setattr(
        route_module.requests,
        "post",
        lambda *args, **kwargs: FakeViewerResponse(),
    )

    payload, status_code = route_module._chamar_viewer_exame(823525)

    assert status_code == 200
    assert payload["message"] == (
        "https://natuslumine.am2saude.com/viewer/viewer/"
        "1.2.410.200001.101.11.302.1100234043.1.20251107073919690"
        "?aet=SP1972&token="
    )


def test_normalizar_base64_pdf_remove_data_url_e_espacos():
    route_module = _load_route_module()

    assert route_module._normalizar_base64_pdf(
        "data:application/pdf;base64, JVBERi0xLjQ=\n"
    ) == "JVBERi0xLjQ="


def test_extrair_viewer_url_usa_message():
    route_module = _load_route_module()

    assert route_module._extrair_viewer_url({
        "message": " https://exemplo.com/viewer?aet=SP1972&token= "
    }) == "https://exemplo.com/viewer?aet=SP1972&token="


def test_exame_para_frontend_marca_tem_imagem(monkeypatch):
    route_module = _load_route_module()
    monkeypatch.setattr(route_module, "_tem_imagem_pacs", lambda id_lancamento: id_lancamento == 823525)

    assert route_module._exame_para_frontend({
        "ID_TOKEN_LANCAMENTO_EXAME": 823525,
        "ID_PACIENTE_SPDATA": 10,
        "NOME_EXAME": "Tomografia",
        "TEM_LAUDO": 1,
    })["temImagem"] is True


def test_tem_imagem_pacs_usa_cache(monkeypatch):
    route_module = _load_route_module()
    monkeypatch.setattr(route_module, "_cache_get_tem_imagem", lambda id_lancamento: True)
    monkeypatch.setattr(route_module, "_chamar_viewer_exame", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("não deveria chamar PACS")))

    assert route_module._tem_imagem_pacs(823525) is True


def test_tem_imagem_pacs_cacheia_resposta_com_message(monkeypatch):
    route_module = _load_route_module()
    chamadas_cache = []
    monkeypatch.setattr(route_module, "_cache_get_tem_imagem", lambda id_lancamento: None)
    monkeypatch.setattr(route_module, "_chamar_viewer_exame", lambda *args, **kwargs: ({"message": "https://exemplo.com/viewer"}, 200))
    monkeypatch.setattr(route_module, "_cache_set_tem_imagem", lambda id_lancamento, tem_imagem: chamadas_cache.append((id_lancamento, tem_imagem)))

    assert route_module._tem_imagem_pacs(823525) is True
    assert chamadas_cache == [(823525, True)]
