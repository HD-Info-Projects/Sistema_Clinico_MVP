from datetime import date, datetime, time

from sqlalchemy import or_, select

from src.models.atendimentos_model import Atendimento
from src.models.documento_medico_model import (
    DocumentoMedico,
    TIPO_ATESTADO,
    TIPO_ENCAMINHAMENTO,
    TIPO_SOLICITACAO_PROCEDIMENTO,
    TIPOS_DOCUMENTO_VALIDOS,
)
from src.models.medico_model import Medico
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.models.usuario_model import Usuario
from src.services.spdata_atendimentos_service import (
    get_crm_medico_usuario,
    normalizar_texto,
    spdata_agenda_id_do_atendimento,
)
from src.services.unidades_service import resolver_unidade_usuario
from src.settings.extensions import db


TIPO_ALIASES = {
    "atestado": TIPO_ATESTADO,
    "ATESTADO": TIPO_ATESTADO,
    "encaminhamento": TIPO_ENCAMINHAMENTO,
    "ENCAMINHAMENTO": TIPO_ENCAMINHAMENTO,
    "solicitacao-procedimento": TIPO_SOLICITACAO_PROCEDIMENTO,
    "solicitacao_procedimento": TIPO_SOLICITACAO_PROCEDIMENTO,
    "SOLICITACAO_PROCEDIMENTO": TIPO_SOLICITACAO_PROCEDIMENTO,
}


def normalizar_tipo_documento(tipo):
    tipo_normalizado = TIPO_ALIASES.get(str(tipo or "").strip())
    if not tipo_normalizado or tipo_normalizado not in TIPOS_DOCUMENTO_VALIDOS:
        raise ValueError("Tipo de documento inválido")
    return tipo_normalizado


def parse_data_iso(valor, campo):
    texto = normalizar_texto(valor, 10)
    if not texto:
        raise ValueError(f"{campo} é obrigatório")
    try:
        return datetime.fromisoformat(texto[:10]).date().isoformat()
    except ValueError as exc:
        raise ValueError(f"{campo} inválida") from exc


def snapshot_medico(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)
    medico = db.session.execute(
        select(Medico).where(
            Medico.usuario_id == usuario_id,
            Medico.ativo.is_(True),
        )
    ).scalars().first()

    return {
        "medico": normalizar_texto(getattr(usuario, "nome_completo", None), 255),
        "crm": normalizar_texto(getattr(medico, "crm", None), 50)
        or normalizar_texto(getattr(medico, "crm_atendimento_spdata", None), 50),
        "especialidade": normalizar_texto(getattr(medico, "especialidade", None), 255),
    }


def buscar_spdata_do_medico(med_spdata_atendimento_id, usuario_id, unidade_id=None):
    unidade = resolver_unidade_usuario(usuario_id, unidade_id)
    spdata = db.session.get(MedSpdataAtendimento, med_spdata_atendimento_id)
    if not spdata:
        raise LookupError("Atendimento do SPDATA não encontrado no MedSystem")

    crm_medico_usuario = get_crm_medico_usuario(usuario_id)
    if normalizar_texto(spdata.crm_medico, 50) != crm_medico_usuario:
        raise PermissionError("Atendimento não pertence ao médico autenticado")

    if spdata.unidade_id and spdata.unidade_id != unidade.id:
        raise PermissionError("Atendimento não pertence à unidade selecionada")
    if spdata.id_centro_custo_spdata and spdata.id_centro_custo_spdata != unidade.codigo_spdata_centro_custo:
        raise PermissionError("Atendimento não pertence à unidade selecionada")
    if not spdata.unidade_id:
        spdata.unidade_id = unidade.id

    return spdata


def data_hora_spdata(spdata):
    if spdata.data_hora_entrada:
        return spdata.data_hora_entrada

    data_ref = spdata.data_atendimento or date.today()
    hora_ref = spdata.hora_entrada or time.min
    return datetime.combine(data_ref, hora_ref)


def buscar_atendimento_local(spdata, criar=False):
    spdata_agenda_id = spdata_agenda_id_do_atendimento(spdata)
    filtros = []
    if spdata.spdata_atendimento_id is not None:
        filtros.append(Atendimento.spdata_atendimento_id == spdata.spdata_atendimento_id)
    if spdata_agenda_id is not None:
        filtros.append(Atendimento.spdata_agenda_id == spdata_agenda_id)

    filtros_unidade = []
    if spdata.unidade_id:
        filtros_unidade.append(Atendimento.unidade_id == spdata.unidade_id)
        filtros_unidade.append(Atendimento.unidade_id.is_(None))

    if not filtros:
        if criar:
            raise LookupError("Atendimento do SPDATA sem identificador para vínculo local")
        return None

    where = [or_(*filtros)]
    if filtros_unidade:
        where.append(or_(*filtros_unidade))

    atendimento = db.session.execute(
        select(Atendimento)
        .where(*where)
        .order_by(Atendimento.id.desc())
    ).scalars().first()

    if atendimento or not criar:
        return atendimento

    atendimento = Atendimento(
        spdata_paciente_id=spdata.id_paciente_spdata,
        spdata_agenda_id=spdata_agenda_id,
        spdata_medico_id=spdata.id_medico_spdata,
        paciente_nome=spdata.paciente,
        paciente_cpf=spdata.cpf or "",
        data_atendimento=data_hora_spdata(spdata),
        hora_inicio=spdata.hora_entrada or time.min,
        hora_fim=None,
        spdata_atendimento_id=spdata.spdata_atendimento_id,
        unidade_id=spdata.unidade_id,
    )
    db.session.add(atendimento)
    db.session.flush()
    return atendimento


def pode_editar_spdata(spdata):
    data_ref = spdata.data_atendimento
    if not data_ref and spdata.data_hora_entrada:
        data_ref = spdata.data_hora_entrada.date()
    return data_ref == date.today()


def validar_dados_documento(tipo, dados):
    dados = dados or {}
    if not isinstance(dados, dict):
        raise ValueError("Dados do documento inválidos")

    if tipo == TIPO_ATESTADO:
        dias = dados.get("dias_afastamento") or dados.get("diasAfastamento")
        try:
            dias = int(dias)
        except (TypeError, ValueError) as exc:
            raise ValueError("dias_afastamento inválido") from exc
        if dias <= 0:
            raise ValueError("dias_afastamento deve ser maior que zero")

        return {
            "data_inicio": parse_data_iso(dados.get("data_inicio") or dados.get("dataInicio"), "data_inicio"),
            "dias_afastamento": dias,
        }

    if tipo == TIPO_ENCAMINHAMENTO:
        encaminhar_para = normalizar_texto(dados.get("encaminhar_para") or dados.get("encaminharPara"), 255)
        if not encaminhar_para:
            raise ValueError("encaminhar_para é obrigatório")

        return {
            "data": parse_data_iso(dados.get("data"), "data"),
            "encaminhar_para": encaminhar_para,
            "profissional_externo": normalizar_texto(
                dados.get("profissional_externo") or dados.get("profissionalExterno"),
                255,
            ) or "",
        }

    if tipo == TIPO_SOLICITACAO_PROCEDIMENTO:
        descricao = normalizar_texto(dados.get("descricao"))
        if not descricao:
            raise ValueError("descricao é obrigatória")

        return {
            "data": parse_data_iso(dados.get("data"), "data"),
            "descricao": descricao,
        }

    raise ValueError("Tipo de documento inválido")


def documento_para_dict(documento, med_spdata_atendimento_id, pode_editar):
    return {
        "id": documento.id,
        "atendimentoId": documento.atendimento_id,
        "medSpdataAtendimentoId": med_spdata_atendimento_id,
        "tipoDocumento": documento.tipo_documento,
        "dados": documento.dados or {},
        "createdAt": documento.created_at.isoformat() if documento.created_at else None,
        "updatedAt": documento.updated_at.isoformat() if documento.updated_at else None,
        "podeEditar": pode_editar,
    }


def listar_documentos_por_ids(usuario_id, ids, unidade_id=None):
    documentos = []
    for med_spdata_atendimento_id in ids:
        spdata = buscar_spdata_do_medico(med_spdata_atendimento_id, usuario_id, unidade_id=unidade_id)
        atendimento = buscar_atendimento_local(spdata, criar=False)
        if not atendimento:
            continue

        pode_editar = pode_editar_spdata(spdata)
        for documento in atendimento.documentos_medicos:
            documentos.append(documento_para_dict(documento, spdata.id, pode_editar))

    return documentos


def listar_documentos_atendimento(usuario_id, med_spdata_atendimento_id, unidade_id=None):
    return listar_documentos_por_ids(usuario_id, [med_spdata_atendimento_id], unidade_id=unidade_id)


def salvar_documento(usuario_id, med_spdata_atendimento_id, tipo, dados, unidade_id=None):
    tipo = normalizar_tipo_documento(tipo)
    spdata = buscar_spdata_do_medico(med_spdata_atendimento_id, usuario_id, unidade_id=unidade_id)
    if not pode_editar_spdata(spdata):
        raise PermissionError("Documentos de atendimentos passados só podem ser impressos")

    atendimento = buscar_atendimento_local(spdata, criar=True)
    dados_normalizados = {
        **validar_dados_documento(tipo, dados),
        **snapshot_medico(usuario_id),
    }

    documento = db.session.execute(
        select(DocumentoMedico).where(
            DocumentoMedico.atendimento_id == atendimento.id,
            DocumentoMedico.tipo_documento == tipo,
        )
    ).scalars().first()

    if documento is None:
        documento = DocumentoMedico(
            atendimento_id=atendimento.id,
            tipo_documento=tipo,
            dados=dados_normalizados,
        )
        db.session.add(documento)
    else:
        documento.dados = dados_normalizados
        documento.updated_at = datetime.utcnow()

    db.session.commit()
    return documento_para_dict(documento, spdata.id, True)
