from types import SimpleNamespace
import time

from src import create_app
from src.controllers.login_controller import LoginController
from flask_jwt_extended import create_access_token

from src.routes.dashboard_route import _item_dashboard
from src.security.decorators import active_user_required, roles_required
from src.security.jwt_blocklist import is_jti_revoked, revoke_jti
from src.security.passwords import (
    hash_password,
    is_hashed_password,
    validate_password_strength,
    verify_password,
)
from src.services.auditoria_service import registrar_auditoria
from src.settings.extensions import db


def test_hash_password_nao_armazena_senha_em_texto_puro():
    senha = "senha-segura"

    senha_hash = hash_password(senha)

    assert senha_hash != senha
    assert is_hashed_password(senha_hash)
    assert verify_password(senha_hash, senha) == (True, False)
    assert verify_password(senha_hash, "senha-incorreta") == (False, False)


def test_verify_password_identifica_senha_legada_em_texto_puro():
    assert verify_password("senha-legada", "senha-legada") == (True, True)
    assert verify_password("senha-legada", "outra-senha") == (False, True)


def test_validate_password_strength_rejeita_senha_fraca():
    try:
        validate_password_strength("123")
    except ValueError as exc:
        assert "pelo menos" in str(exc)
    else:
        raise AssertionError("Senha fraca deveria ser rejeitada")


def test_login_controller_migra_senha_legada_para_hash(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = app.config.get("JWT_SECRET_KEY") or "test-secret"

    usuario = SimpleNamespace(
        id=123,
        email="medico@example.com",
        nome_completo="Médico Teste",
        role="medico",
        senha="senha-legada",
        medico=None,
    )

    def set_senha(senha):
        usuario.senha = hash_password(senha)

    usuario.set_senha = set_senha

    controller = LoginController()
    monkeypatch.setattr(
        controller,
        "_LoginController__repo",
        SimpleNamespace(get_usuario=lambda _email: usuario),
    )

    commits = []
    monkeypatch.setattr(db.session, "commit", lambda: commits.append(True))

    with app.app_context():
        token = controller.generate_JWT_usuario("medico@example.com", "senha-legada")

    assert token
    assert commits == [True]
    assert is_hashed_password(usuario.senha)
    assert verify_password(usuario.senha, "senha-legada") == (True, False)


def test_login_controller_rejeita_usuario_inativo(monkeypatch):
    usuario = SimpleNamespace(
        id=123,
        email="medico@example.com",
        nome_completo="Médico Teste",
        role="medico",
        senha=hash_password("senha-segura"),
        medico=None,
        ativo=False,
        bloqueado_em=None,
    )

    controller = LoginController()
    monkeypatch.setattr(
        controller,
        "_LoginController__repo",
        SimpleNamespace(get_usuario=lambda _email: usuario),
    )

    assert controller.generate_JWT_usuario("medico@example.com", "senha-segura") is None


def test_login_controller_bloqueia_usuario_apos_tentativas_falhas(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = app.config.get("JWT_SECRET_KEY") or "test-secret"
    app.config["LOGIN_MAX_FAILED_ATTEMPTS"] = 2
    app.config["LOGIN_ACCOUNT_LOCK_ENABLED"] = True

    usuario = SimpleNamespace(
        id=123,
        email="medico@example.com",
        nome_completo="Médico Teste",
        role="medico",
        senha=hash_password("senha-correta"),
        medico=None,
        ativo=True,
        bloqueado_em=None,
        bloqueio_motivo=None,
        tentativas_login_falhas=0,
        ultimo_login_falho_em=None,
    )

    controller = LoginController()
    monkeypatch.setattr(
        controller,
        "_LoginController__repo",
        SimpleNamespace(get_usuario=lambda _email: usuario),
    )

    commits = []
    monkeypatch.setattr(db.session, "commit", lambda: commits.append(True))

    with app.app_context():
        assert controller.generate_JWT_usuario("medico@example.com", "senha-errada") is None
        assert usuario.tentativas_login_falhas == 1
        assert usuario.bloqueado_em is None

        assert controller.generate_JWT_usuario("medico@example.com", "senha-errada") is None

    assert commits == [True, True]
    assert usuario.tentativas_login_falhas == 2
    assert usuario.bloqueado_em is not None
    assert usuario.bloqueio_motivo == "Excesso de tentativas de login falhas"


def test_registrar_auditoria_grava_metadados_sem_banco_real(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True

    eventos = []
    monkeypatch.setattr(db.session, "add", lambda evento: eventos.append(evento))
    monkeypatch.setattr(db.session, "commit", lambda: None)

    with app.test_request_context(
        "/prontuario/historico-paciente/10",
        headers={
            "X-Forwarded-For": "203.0.113.10, 10.0.0.1",
            "User-Agent": "pytest",
        },
    ):
        evento = registrar_auditoria(
            "VISUALIZOU_HISTORICO_BIODATA",
            entidade="paciente",
            entidade_id=10,
            usuario_id=123,
            descricao="Acesso ao histórico BioData do paciente",
        )

    assert evento is eventos[0]
    assert evento.acao == "VISUALIZOU_HISTORICO_BIODATA"
    assert evento.entidade == "paciente"
    assert evento.entidade_id == 10
    assert evento.usuario_id == 123
    assert evento.ip == "203.0.113.10"
    assert evento.user_agent == "pytest"


def test_registrar_auditoria_remove_cpf_token_e_senha(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True

    eventos = []
    monkeypatch.setattr(db.session, "add", lambda evento: eventos.append(evento))
    monkeypatch.setattr(db.session, "commit", lambda: None)

    with app.test_request_context("/auditoria"):
        evento = registrar_auditoria(
            "TESTE_SANITIZACAO",
            entidade="teste",
            descricao="cpf=123.456.789-00 token=abc123 senha=segredo",
        )

    assert evento is eventos[0]
    assert "123.456.789-00" not in evento.descricao
    assert "abc123" not in evento.descricao
    assert "segredo" not in evento.descricao
    assert "[CPF_REMOVIDO]" in evento.descricao
    assert "token=[REMOVIDO]" in evento.descricao
    assert "senha=[REMOVIDO]" in evento.descricao


def test_jwt_blocklist_revoga_jti_em_memoria():
    app = create_app()
    app.config["JWT_BLOCKLIST_STORAGE_URI"] = "memory://"

    with app.app_context():
        revoke_jti("jti-teste", time.time() + 60)
        assert is_jti_revoked("jti-teste") is True


def test_roles_required_rejeita_usuario_inativo(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = app.config.get("JWT_SECRET_KEY") or "test-secret"

    @app.get("/rota-segura-teste")
    @roles_required("medico")
    def rota_segura_teste():
        return {"ok": True}

    with app.app_context():
        token = create_access_token(identity="123", additional_claims={"role": "medico"})

    monkeypatch.setattr(
        db.session,
        "get",
        lambda _model, _id: SimpleNamespace(id=123, role="medico", ativo=False, bloqueado_em=None),
    )
    monkeypatch.setattr(
        "src.security.decorators.registrar_auditoria",
        lambda *args, **kwargs: None,
    )

    with app.test_client() as client:
        response = client.get(
            "/rota-segura-teste",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401


def test_active_user_required_rejeita_usuario_bloqueado_sem_role(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = app.config.get("JWT_SECRET_KEY") or "test-secret"

    @app.get("/rota-ativa-teste")
    @active_user_required()
    def rota_ativa_teste():
        return {"ok": True}

    with app.app_context():
        token = create_access_token(identity="123", additional_claims={"role": "medico"})

    monkeypatch.setattr(
        db.session,
        "get",
        lambda _model, _id: SimpleNamespace(id=123, role="medico", ativo=True, bloqueado_em="2026-08-17"),
    )
    monkeypatch.setattr(
        "src.security.decorators.registrar_auditoria",
        lambda *args, **kwargs: None,
    )

    with app.test_client() as client:
        response = client.get(
            "/rota-ativa-teste",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401


def test_tts_desabilitado_por_configuracao():
    app = create_app()
    app.config["TESTING"] = True
    app.config["ENABLE_TTS"] = False

    with app.test_client() as client:
        response = client.post("/tts/speak", json={"text": "Paciente, sala 1"})

    assert response.status_code == 503


def test_tts_bloqueia_texto_clinico():
    app = create_app()
    app.config["TESTING"] = True
    app.config["ENABLE_TTS"] = True

    with app.test_client() as client:
        response = client.post("/tts/speak", json={"text": "Paciente com CID A00"})

    assert response.status_code == 400


def test_tts_auditoria_nao_grava_texto_falado(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    app.config["ENABLE_TTS"] = True

    async def gerar_audio_fake(_texto, _voice):
        return b"audio"

    eventos = []
    monkeypatch.setattr("src.routes.tts_route._gerar_audio_edge_tts", gerar_audio_fake)
    monkeypatch.setattr(
        "src.routes.tts_route.registrar_auditoria",
        lambda *args, **kwargs: eventos.append(kwargs),
    )

    with app.test_client() as client:
        response = client.post(
            "/tts/speak",
            json={"text": "Paciente 12, sala 3", "chamadoId": 42},
        )

    assert response.status_code == 200
    assert eventos[0]["entidade"] == "tts"
    assert eventos[0]["entidade_id"] == 42
    assert "Paciente 12" not in eventos[0]["descricao"]
    assert "tamanho_texto=" in eventos[0]["descricao"]


def test_dashboard_remove_identificadores_desnecessarios():
    item = _item_dashboard(
        {
            "id": 1,
            "pacienteId": 22,
            "data": "2026-08-04",
            "horario": "10:30",
            "paciente": {
                "nome": "Paciente Teste",
                "cpf": "12345678900",
                "email": "paciente@example.test",
                "telefone": "11999999999",
                "endereco": "Rua Teste",
            },
        },
        "12345",
    )

    assert item["PACIENTE"] == "Paciente Teste"
    assert item["CPF"] == ""
    assert item["EMAIL"] == ""
    assert item["ENDERECO"] == ""
