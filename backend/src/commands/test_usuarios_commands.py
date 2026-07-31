from src import create_app
from src.commands.usuarios_commands import _registrar_usuario_local
from src.security.passwords import is_hashed_password, verify_password
from src.settings.extensions import db


class QuerySemUsuario:
    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return None


def test_registrar_usuario_dpo_cria_role_dpo_com_senha_hash(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    adicionados = []
    commits = []

    monkeypatch.setattr(db.session, "query", lambda _model: QuerySemUsuario())
    monkeypatch.setattr(db.session, "add", lambda usuario: adicionados.append(usuario))
    monkeypatch.setattr(db.session, "commit", lambda: commits.append(True))

    with app.app_context():
        usuario, acao = _registrar_usuario_local(
            "DPO LGPD",
            "00000000000",
            "DPO@EXAMPLE.COM",
            "senha-segura",
            "dpo",
            atualizar=False,
        )

    assert acao == "criado"
    assert adicionados == [usuario]
    assert commits == [True]
    assert usuario.role == "dpo"
    assert usuario.email == "dpo@example.com"
    assert is_hashed_password(usuario.senha)
    assert verify_password(usuario.senha, "senha-segura") == (True, False)
