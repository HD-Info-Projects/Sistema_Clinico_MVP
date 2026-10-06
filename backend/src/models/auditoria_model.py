from datetime import datetime, timezone
from enum import Enum
from ipaddress import ip_address, ip_network
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app, has_app_context

from src.settings.extensions import db

"""  
    Registra ações importantes do sistema.
"""

class AcaoAuditoria(Enum):
    LOGIN_SUCESSO = "LOGIN_SUCESSO"
    LOGIN_FALHA = "LOGIN_FALHA"
    DESBLOQUEOU_USUARIO = "DESBLOQUEOU_USUARIO"
    LOGOUT = "LOGOUT"
    ACESSO_NEGADO = "ACESSO_NEGADO"
    VISUALIZOU_PRONTUARIO = "VISUALIZOU_PRONTUARIO"
    VISUALIZOU_HISTORICO_BIODATA = "VISUALIZOU_HISTORICO_BIODATA"
    VISUALIZOU_HISTORICO_SPDATA = "VISUALIZOU_HISTORICO_SPDATA"
    VISUALIZOU_EXAMES_PACS = "VISUALIZOU_EXAMES_PACS"
    VISUALIZOU_LAUDO_EXAME = "VISUALIZOU_LAUDO_EXAME"
    VISUALIZOU_IMAGEM_EXAME = "VISUALIZOU_IMAGEM_EXAME"
    VISUALIZOU_AGENDA = "VISUALIZOU_AGENDA"
    VISUALIZOU_CHECK_IN = "VISUALIZOU_CHECK_IN"
    VISUALIZOU_NO_SHOW = "VISUALIZOU_NO_SHOW"
    VISUALIZOU_RETENCAO_EXAMES = "VISUALIZOU_RETENCAO_EXAMES"
    VISUALIZOU_DOCUMENTOS_MEDICOS = "VISUALIZOU_DOCUMENTOS_MEDICOS"
    SALVOU_DOCUMENTO_MEDICO = "SALVOU_DOCUMENTO_MEDICO"
    ALTEROU_STATUS_AGENDA = "ALTEROU_STATUS_AGENDA"
    ALTEROU_PRIORIDADE_ATENDIMENTO = "ALTEROU_PRIORIDADE_ATENDIMENTO"
    ALTEROU_MOTIVO_NO_SHOW = "ALTEROU_MOTIVO_NO_SHOW"
    INICIOU_ATENDIMENTO = "INICIOU_ATENDIMENTO"
    EDITOU_EVOLUCAO = "EDITOU_EVOLUCAO"
    FINALIZOU_ATENDIMENTO = "FINALIZOU_ATENDIMENTO"
    CRIOU_MODELO_MEDICO = "CRIOU_MODELO_MEDICO"
    EDITOU_MODELO_MEDICO = "EDITOU_MODELO_MEDICO"
    EXCLUIU_MODELO_MEDICO = "EXCLUIU_MODELO_MEDICO"
    TTS_SOLICITADO = "TTS_SOLICITADO"
    GEROU_RECEITA = "GEROU_RECEITA"
    GEROU_ATESTADO = "GEROU_ATESTADO"
    EXPORTOU_DADOS = "EXPORTOU_DADOS"
    SINCRONIZOU_SPDATA = "SINCRONIZOU_SPData"
    RETENCAO_DESCARTE_EXECUTADA = "RETENCAO_DESCARTE_EXECUTADA"
    ENTROU_MODULO = "ENTROU_MODULO"
    SAIU_MODULO = "SAIU_MODULO"
    TROCOU_ACESSO = "TROCOU_ACESSO"
    MUDOU_UNIDADE = "MUDOU_UNIDADE"
    ABRIU_PACIENTE = "ABRIU_PACIENTE"
    CANCELOU_ACAO = "CANCELOU_ACAO"


ACAO_LABELS = {
    "LOGIN_SUCESSO": "Login",
    "LOGIN_FALHA": "Falha de login",
    "LOGOUT": "Logoff",
    "ACESSO_NEGADO": "Acesso negado",
    "DESBLOQUEOU_USUARIO": "Desbloqueio de usuario",
    "VISUALIZOU_PRONTUARIO": "Visualizacao de prontuario",
    "VISUALIZOU_HISTORICO_BIODATA": "Visualizacao de historico BioData",
    "VISUALIZOU_HISTORICO_SPDATA": "Visualizacao de historico SPDATA",
    "VISUALIZOU_EXAMES_PACS": "Visualizacao de exames PACS",
    "VISUALIZOU_LAUDO_EXAME": "Visualizacao de laudo",
    "VISUALIZOU_IMAGEM_EXAME": "Visualizacao de imagem",
    "VISUALIZOU_AGENDA": "Visualizacao de agenda",
    "VISUALIZOU_CHECK_IN": "Visualizacao do dashboard da recepcao",
    "VISUALIZOU_NO_SHOW": "Visualizacao de no-show",
    "VISUALIZOU_RETENCAO_EXAMES": "Visualizacao de conversao de exames",
    "VISUALIZOU_DOCUMENTOS_MEDICOS": "Visualizacao de documentos medicos",
    "SALVOU_DOCUMENTO_MEDICO": "Salvamento de documento medico",
    "ALTEROU_STATUS_AGENDA": "Alteracao de status da agenda",
    "ALTEROU_PRIORIDADE_ATENDIMENTO": "Alteracao de prioridade",
    "ALTEROU_MOTIVO_NO_SHOW": "Alteracao de motivo de no-show",
    "INICIOU_ATENDIMENTO": "Inicio de atendimento",
    "EDITOU_EVOLUCAO": "Edicao de evolucao",
    "FINALIZOU_ATENDIMENTO": "Finalizacao de atendimento",
    "CRIOU_MODELO_MEDICO": "Criacao de padrao medico",
    "EDITOU_MODELO_MEDICO": "Edicao de padrao medico",
    "EXCLUIU_MODELO_MEDICO": "Exclusao de padrao medico",
    "TTS_SOLICITADO": "Chamada por voz",
    "GEROU_RECEITA": "Geracao de receita",
    "GEROU_ATESTADO": "Geracao de atestado",
    "EXPORTOU_DADOS": "Exportacao de dados",
    "SINCRONIZOU_SPDATA": "Sincronizacao SPDATA",
    "SINCRONIZOU_SPData": "Sincronizacao SPDATA",
    "RETENCAO_DESCARTE_EXECUTADA": "Descarte por retencao LGPD",
    "ENTROU_MODULO": "Entrada em modulo",
    "SAIU_MODULO": "Saida de modulo",
    "TROCOU_ACESSO": "Troca de acesso",
    "MUDOU_UNIDADE": "Mudanca de unidade",
    "ABRIU_PACIENTE": "Abertura de paciente",
    "CANCELOU_ACAO": "Cancelamento",
}


ENTIDADE_LABELS = {
    "usuarios": "Usuario",
    "login": "Login",
    "logout": "Logoff",
    "rota": "Rota",
    "modulo": "Modulo",
    "acesso": "Acesso",
    "unidade": "Unidade",
    "paciente": "Paciente",
    "paciente_spdata": "Paciente SPDATA",
    "atendimento_spdata": "Atendimento SPDATA",
    "novo_atendimento_spdata": "Cadastro de Atendimento",
    "agenda_medica": "Agenda medica",
    "agenda_assistente": "Dashboard do assistente",
    "check_in": "Dashboard da recepcao",
    "atendimento_prioridade": "Prioridade de atendimento",
    "no_show": "No-show",
    "retencao_exames": "Conversao de exames",
    "documentos_medicos": "Documentos medicos",
    "documentos_medicos_personalizados": "Documentos personalizados",
    "med_spdata_atendimentos": "Atendimento medico",
    "tts": "Chamada por voz",
}


DESCRICOES_PADRAO = {
    "LOGIN_SUCESSO": "Login realizado com sucesso.",
    "LOGIN_FALHA": "Tentativa de login negada.",
    "LOGOUT": "Logoff realizado.",
    "ACESSO_NEGADO": "Tentativa de acesso bloqueada por permissao.",
    "ENTROU_MODULO": "Usuario entrou no modulo.",
    "SAIU_MODULO": "Usuario saiu do modulo.",
    "TROCOU_ACESSO": "Usuario trocou o modo de acesso.",
    "MUDOU_UNIDADE": "Usuario mudou a unidade ativa.",
    "ABRIU_PACIENTE": "Usuario abriu dados de paciente.",
    "CANCELOU_ACAO": "Usuario cancelou a acao em tela.",
}


def _config_timezone():
    nome = "America/Sao_Paulo"
    if has_app_context():
        nome = current_app.config.get("AUDITORIA_TIMEZONE", nome)
    try:
        return ZoneInfo(nome)
    except ZoneInfoNotFoundError:
        return ZoneInfo("America/Sao_Paulo")


def _utc_aware(valor):
    if not valor:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def _created_at_utc_iso(valor):
    data = _utc_aware(valor)
    return data.isoformat().replace("+00:00", "Z") if data else None


def _created_at_local_iso(valor):
    data = _utc_aware(valor)
    return data.astimezone(_config_timezone()).isoformat() if data else None


def _fixed_ip_networks():
    if not has_app_context():
        return []

    redes = []
    for valor in current_app.config.get("NATUS_FIXED_IPS", []):
        try:
            redes.append(ip_network(valor, strict=False))
        except ValueError:
            continue
    return redes


def _ip_origem(valor):
    if not valor:
        return "Nao identificado"

    try:
        ip = ip_address(str(valor).strip())
    except ValueError:
        return "IP invalido"

    if any(ip in rede for rede in _fixed_ip_networks()):
        return "Natus"
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        return "Rede privada/local"
    return "Externo / nao cadastrado"


def _label_acao(acao):
    texto = acao.value if hasattr(acao, "value") else str(acao or "")
    return ACAO_LABELS.get(texto, texto.replace("_", " ").capitalize())


def _label_entidade(entidade):
    if not entidade:
        return "-"
    return ENTIDADE_LABELS.get(entidade, str(entidade).replace("_", " ").capitalize())


def _descricao_direta(acao, descricao):
    texto_acao = acao.value if hasattr(acao, "value") else str(acao or "")
    texto = str(descricao or "").strip()
    if not texto:
        return DESCRICOES_PADRAO.get(texto_acao, _label_acao(texto_acao))

    substituicoes = {
        "Listagem de": "Visualizacao de",
        "Acesso ao": "Visualizacao do",
        "Acesso à": "Visualizacao da",
        "Acesso a": "Visualizacao de",
        "criado/atualizado": "salvo/atualizado",
        "criado/sincronizado": "salvo/sincronizado",
    }
    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)
    return texto


class Auditoria(db.Model):
    __tablename__ = "auditorias"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    medico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    acao = db.Column(
        db.String(100),
        nullable=False
    )

    entidade = db.Column(
        db.String(100),
        nullable=True
    )

    entidade_id = db.Column(
        db.Integer,
        nullable=True
    )

    descricao = db.Column(
        db.Text,
        nullable=True
    )

    ip = db.Column(
        db.String(100),
        nullable=True
    )

    user_agent = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[usuario_id],
        back_populates="auditorias"
    )

    medico = db.relationship(
        "Usuario",
        foreign_keys=[medico_id],
        back_populates="auditorias_medicas"
    )

    def __repr__(self):
        acao = self.acao.value if hasattr(self.acao, "value") else self.acao
        return (
            f"<Auditoria acao={acao} "
            f"entidade={self.entidade} "
            f"entidade_id={self.entidade_id}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "medico_id": self.medico_id,
            "acao": self.acao.value if hasattr(self.acao, "value") else self.acao,
            "entidade": self.entidade,
            "entidade_id": self.entidade_id,
            "descricao": self.descricao,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "created_at": _created_at_local_iso(self.created_at),
            "created_at_utc": _created_at_utc_iso(self.created_at),
            "acao_label": _label_acao(self.acao),
            "entidade_label": _label_entidade(self.entidade),
            "descricao_direta": _descricao_direta(self.acao, self.descricao),
            "ip_origem": _ip_origem(self.ip),
            "usuario": {
                "id": self.usuario.id,
                "nome_completo": self.usuario.nome_completo,
                "email": self.usuario.email,
                "role": self.usuario.role,
            } if self.usuario else None,
        }
