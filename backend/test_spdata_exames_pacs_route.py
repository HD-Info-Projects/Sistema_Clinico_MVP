import importlib.util
from pathlib import Path

from flask import Flask


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
            "url": "https://exemplo.com/imagem",
            "treatmentId": "823525",
        }


def test_busca_exames_pacs_envia_treatment_id_823525(monkeypatch):
    route_module = _load_route_module()
    app = Flask(__name__)
    app.register_blueprint(route_module.exames_pacs_bp)
    chamadas = []

    def post_fake(url, headers=None, json=None, timeout=None):
        chamadas.append({
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
        })
        return FakeResponse()

    monkeypatch.setattr(route_module.requests, "post", post_fake)

    with app.test_client() as client:
        response = client.post("/exames-pacs/823525")

    assert response.status_code == 200
    assert response.get_json() == {
        "url": "https://exemplo.com/imagem",
        "treatmentId": "823525",
    }
    assert chamadas == [{
        "url": route_module.URL,
        "headers": {
            "Authorization": f"Bearer {route_module.TOKEN}",
            "Content-Type": "application/json",
        },
        "json": {"treatmentId": "823525"},
        "timeout": 15,
    }]
