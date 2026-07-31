from types import SimpleNamespace

from src import create_app
from src.controllers.login_controller import LoginController
from src.security.passwords import hash_password, is_hashed_password, verify_password
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
