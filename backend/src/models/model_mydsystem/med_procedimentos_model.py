from datetime import datetime

from src.settings.extensions import db


class Procedimento(db.Model):
    __tablename__ = "procedimentos"
    __table_args__ = (
        db.UniqueConstraint(
            "tab",
            "codigo_procedimento",
            name="uq_procedimentos_tab_codigo",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    spdata_tp_id = db.Column(db.Integer, nullable=False, index=True)
    id_tbctrthm = db.Column(db.Integer, nullable=False, index=True)
    codigo_procedimento = db.Column(db.BigInteger, nullable=False, index=True)
    tab = db.Column(db.Integer, nullable=False, index=True)

    nome = db.Column(db.String(255), nullable=False, index=True)
    apelido_procedimento = db.Column(db.String(100), nullable=True, index=True)
    tipo_modulo = db.Column(db.String(10), nullable=True)

    tipo_ato_codigo = db.Column(db.Integer, nullable=True, index=True)
    tipo_ato_nome = db.Column(db.String(100), nullable=True, index=True)

    centro_tabela_nome = db.Column(db.String(100), nullable=True)
    centro_tabela_situacao = db.Column(db.String(10), nullable=True)
    situacao = db.Column(db.String(10), nullable=True, index=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    ch = db.Column(db.Float, nullable=True)
    aux = db.Column(db.Integer, nullable=True)
    filme = db.Column(db.Float, nullable=True)
    cope = db.Column(db.Float, nullable=True)

    procmed = db.Column(db.String(10), nullable=True)
    stand = db.Column(db.String(10), nullable=True)
    pacote = db.Column(db.String(10), nullable=True)

    tab_ref = db.Column(db.Integer, nullable=True)
    proc_ref = db.Column(db.BigInteger, nullable=True)
    tab_ref_tuss = db.Column(db.Integer, nullable=True)
    proc_ref_tuss = db.Column(db.BigInteger, nullable=True)

    exige_autorizacao = db.Column(db.Integer, nullable=True)
    qtde_max_guia = db.Column(db.Integer, nullable=True)
    bloqueio = db.Column(db.String(10), nullable=True)

    dados_spdata = db.Column(db.JSON, nullable=True)

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    atualizado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self):
        return f"<Procedimento {self.tab}/{self.codigo_procedimento} - {self.nome}>"
