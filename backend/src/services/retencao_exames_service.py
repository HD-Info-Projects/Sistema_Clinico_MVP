from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import or_, select

from src.models.atendimentos_model import Atendimento
from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.model_mydsystem.med_exames_model import Exame
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.models.model_mydsystem.med_spdata_convenios_model import MedSpdataConvenio
from src.models.solicitacao_exame_model import SolicitacaoExame, StatusSolicitacaoExame
from src.settings.extensions import db
from src.utils.normalizar import normalizar_cpf


PRAZO_NAO_CONVERTIDO = timedelta(days=90)


def normalizar_valor(valor):
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.isoformat()
    return valor


def row_para_dict(row, nomes_colunas):
    return {
        nome: normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def numero(valor):
    if valor is None or valor == "":
        return 0
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0


def normalizar_int(valor):
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        try:
            return int(float(str(valor).replace(",", ".")))
        except (TypeError, ValueError):
            return None


def valor_para_data(valor):
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor[:10]).date()
        except ValueError:
            return None
    return None


def data_iso(valor):
    data_ref = valor_para_data(valor)
    return data_ref.isoformat() if data_ref else ""


def dias_desde(valor, hoje=None):
    data_ref = valor_para_data(valor)
    if not data_ref:
        return 0
    hoje = hoje or date.today()
    return max((hoje - data_ref).days, 0)


def data_hora_inicial(valor):
    return datetime.combine(valor, time.min)


def data_hora_final(valor):
    return datetime.combine(valor, time.max)


def placeholders(valores):
    return ", ".join("?" for _ in valores)


def codigo_exame(exame):
    return texto(getattr(exame, "codigo_alfanumerico", None)).upper()


def ato_exame(exame):
    return texto(getattr(exame, "ato", None))


def normalizar_nome_exame(valor):
    return texto(valor).upper()


def nome_exame_solicitacao(solicitacao, exame):
    return texto(getattr(exame, "nome", None)) or texto(solicitacao.tipo_exame)


def cpf_normalizado(*valores):
    for valor in valores:
        cpf = normalizar_cpf(valor)
        if cpf:
            return cpf
    return ""


def buscar_solicitacoes_locais(data_ini, data_fim, unidade=None):
    filtros = [
        SolicitacaoExame.created_at >= data_hora_inicial(data_ini),
        SolicitacaoExame.created_at <= data_hora_final(data_fim),
        SolicitacaoExame.status != StatusSolicitacaoExame.CANCELADO,
    ]

    if unidade:
        filtros.append(or_(
            Atendimento.unidade_id == unidade.id,
            MedSpdataAtendimento.unidade_id == unidade.id,
            MedSpdataAtendimento.id_centro_custo_spdata == unidade.codigo_spdata_centro_custo,
        ))

    stmt = (
        select(
            SolicitacaoExame,
            Atendimento,
            Exame,
            MedSpdataAtendimento,
            MedSpdataConvenio,
        )
        .join(Atendimento, SolicitacaoExame.atendimento_id == Atendimento.id)
        .outerjoin(Exame, SolicitacaoExame.exame_id == Exame.id)
        .outerjoin(
            MedSpdataAtendimento,
            Atendimento.spdata_atendimento_id == MedSpdataAtendimento.spdata_atendimento_id,
        )
        .outerjoin(
            MedSpdataConvenio,
            MedSpdataAtendimento.id_convenio_spdata == MedSpdataConvenio.codigo_spdata,
        )
        .where(*filtros)
        .order_by(SolicitacaoExame.created_at.desc(), SolicitacaoExame.id.desc())
    )

    return db.session.execute(stmt).all()


def parametros_busca_spdata(registros_locais):
    codigos = sorted({
        codigo_exame(exame)
        for _, _, exame, _, _ in registros_locais
        if codigo_exame(exame)
    })
    nomes_sem_codigo = sorted({
        normalizar_nome_exame(nome_exame_solicitacao(solicitacao, exame))
        for solicitacao, _, exame, _, _ in registros_locais
        if not codigo_exame(exame)
        and normalizar_nome_exame(nome_exame_solicitacao(solicitacao, exame))
    })
    ids_pacientes = sorted({
        paciente_id
        for _, atendimento, _, spdata, _ in registros_locais
        for paciente_id in (
            normalizar_int(atendimento.spdata_paciente_id),
            normalizar_int(getattr(spdata, "id_paciente_spdata", None)),
        )
        if paciente_id is not None
    })
    cpfs = sorted({
        cpf
        for _, atendimento, _, spdata, _ in registros_locais
        for cpf in (
            cpf_normalizado(atendimento.paciente_cpf),
            cpf_normalizado(getattr(spdata, "cpf", None)),
        )
        if cpf
    })
    prontuarios = sorted({
        prontuario
        for _, _, _, spdata, _ in registros_locais
        if (prontuario := texto(getattr(spdata, "prontuario", None)))
    })

    datas = [
        solicitacao.created_at.date()
        for solicitacao, *_ in registros_locais
        if solicitacao.created_at
    ]

    return {
        "codigos": codigos,
        "nomes_sem_codigo": nomes_sem_codigo,
        "ids_pacientes": ids_pacientes,
        "cpfs": cpfs,
        "prontuarios": prontuarios,
        "data_ini": min(datas) if datas else None,
        "data_fim": date.today(),
    }


def buscar_realizacoes_spdata(registros_locais, unidade=None):
    params = parametros_busca_spdata(registros_locais)
    codigos = params["codigos"]
    nomes_sem_codigo = params["nomes_sem_codigo"]
    filtros_exame = []
    filtros_paciente = []
    valores = [params["data_ini"], params["data_fim"]]

    if not registros_locais or not params["data_ini"] or not (codigos or nomes_sem_codigo):
        return []

    if codigos:
        filtros_exame.append(f"SIL.EXAME IN ({placeholders(codigos)})")
        valores.extend(codigos)

    if nomes_sem_codigo:
        filtros_exame.append(f"UPPER(PROC.NOME) IN ({placeholders(nomes_sem_codigo)})")
        valores.extend(nomes_sem_codigo)

    if params["ids_pacientes"]:
        filtros_paciente.append(
            f"COALESCE(PAC_ATEND.ID, PAC_PRONT.ID) IN ({placeholders(params['ids_pacientes'])})"
        )
        valores.extend(params["ids_pacientes"])

    if params["cpfs"]:
        filtros_paciente.append(
            f"COALESCE(PAC_ATEND.CPF, PAC_PRONT.CPF) IN ({placeholders(params['cpfs'])})"
        )
        valores.extend(params["cpfs"])

    if params["prontuarios"]:
        filtros_paciente.append(f"SIC.PRONT IN ({placeholders(params['prontuarios'])})")
        valores.extend(params["prontuarios"])

    if not filtros_paciente:
        return []

    filtro_unidade = ""
    if unidade and unidade.codigo_spdata_centro_custo is not None:
        filtro_unidade = " AND ATD.ID_TBCENCUS = ?"
        valores.append(unidade.codigo_spdata_centro_custo)

    sql = f"""
        SELECT
            SIL.ID AS ID_EXAME_LANCAMENTO,
            SIL.ID_SICADATE,
            SIC.ID_ATCABECATEND,
            SIC.PRONT,
            COALESCE(PAC_ATEND.ID, PAC_PRONT.ID) AS ID_PACIENTE_SPDATA,
            COALESCE(PAC_ATEND.CPF, PAC_PRONT.CPF) AS CPF,
            COALESCE(PAC_ATEND.NOME, PAC_PRONT.NOME, SIC.SEGURADO) AS PACIENTE,
            SIL.DATA AS DATA_EXAME,
            SIL.DATA_HORA_INCLUSAO,
            SIL.EXAME,
            SIL.ATO,
            PROC.NOME AS EXAME_NOME,
            PROC.CODAMB AS CODAMB_PROCEDIMENTO,
            PROC.CODALF AS CODALF_PROCEDIMENTO,
            SIR.CODAMB AS CODAMB_CONVENIO,
            ST.NOME AS STATUS_EXAME,
            SIL.COLETA,
            SIL.PREVISAOCOLETA,
            SIL.DATA_HORA_LIBERA_EXAME,
            SIL.DTEMIRES,
            (
                SELECT FIRST 1
                    COALESCE(VV.VALOR_CH, 0)
                    + COALESCE(VV.VALOR_CO, 0)
                    + COALESCE(VV.VALOR_FILME, 0)
                FROM TBVLRTHM VV
                WHERE VV.TAB = CON.THM_E
                  AND VV.COD = COALESCE(SIR.CODAMB, PROC.CODAMB)
                  AND VV.DATA <= SIL.DATA
                ORDER BY VV.DATA DESC
            ) AS VALOR_ESTIMADO
        FROM SILANEXA SIL
        INNER JOIN SICADATE SIC
            ON SIL.ID_SICADATE = SIC.ID
        INNER JOIN TBCONVEN CON
            ON SIC.CONV = CON.COD
        LEFT JOIN ATCABECATEND ATD
            ON SIC.ID_ATCABECATEND = ATD.ID
        LEFT JOIN RICADPAC PAC_ATEND
            ON PAC_ATEND.ID = ATD.ID_RICADPAC
        LEFT JOIN RICADPAC PAC_PRONT
            ON PAC_PRONT.PRONT = SIC.PRONT
        LEFT JOIN SIREFCON SIR
            ON SIC.CONV = SIR.CONV
           AND SIR.TIPO_CTA = (
                SELECT
                    CASE
                        WHEN V.THM = V.THM_E THEN 'A'
                        ELSE SIC.ATEND
                    END
                FROM TBCONVEN V
                WHERE V.COD = SIC.CONV
            )
           AND SIL.EXAME = SIR.EXAME
           AND SIL.ATO = SIR.ATO
        LEFT JOIN SITABPRO PROC
            ON PROC.CODALF = SIL.EXAME
           AND PROC.ATO = SIL.ATO
        LEFT JOIN PRSITEXAME ST
            ON ST.ID = SIL.ID_PRSITEXAME
        WHERE CAST(SIL.DATA AS DATE) BETWEEN ? AND ?
          AND ({' OR '.join(filtros_exame)})
          AND ({' OR '.join(filtros_paciente)})
          {filtro_unidade}
        ORDER BY SIL.DATA ASC, SIL.ID ASC
    """

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        cursor.execute(sql, tuple(valores))
        nomes_colunas = [desc[0].strip().upper() for desc in cursor.description]
        rows = [row_para_dict(row, nomes_colunas) for row in cursor.fetchall()]
        cursor.close()
        return rows


def indexar_realizacoes(realizacoes):
    indice = defaultdict(list)
    for row in realizacoes:
        codigo = texto(row.get("EXAME")).upper()
        ato = texto(row.get("ATO"))
        if codigo:
            indice[(codigo, ato)].append(row)

        nome = normalizar_nome_exame(row.get("EXAME_NOME"))
        if nome:
            indice[("nome", nome)].append(row)
    return indice


def paciente_compativel(row, atendimento, spdata):
    id_spdata_row = normalizar_int(row.get("ID_PACIENTE_SPDATA"))
    ids_locais = {
        valor
        for valor in (
            normalizar_int(atendimento.spdata_paciente_id),
            normalizar_int(getattr(spdata, "id_paciente_spdata", None)),
        )
        if valor is not None
    }
    if id_spdata_row is not None and id_spdata_row in ids_locais:
        return True

    cpf_row = cpf_normalizado(row.get("CPF"))
    cpfs_locais = {
        cpf
        for cpf in (
            cpf_normalizado(atendimento.paciente_cpf),
            cpf_normalizado(getattr(spdata, "cpf", None)),
        )
        if cpf
    }
    if cpf_row and cpf_row in cpfs_locais:
        return True

    prontuario_row = texto(row.get("PRONT"))
    prontuario_local = texto(getattr(spdata, "prontuario", None))
    return bool(prontuario_row and prontuario_local and prontuario_row == prontuario_local)


def encontrar_realizacao(solicitacao, atendimento, exame, spdata, indice):
    codigo = codigo_exame(exame)
    ato = ato_exame(exame)
    if codigo:
        candidatos = indice.get((codigo, ato), []) or indice.get((codigo, ""), [])
    else:
        nome = normalizar_nome_exame(nome_exame_solicitacao(solicitacao, exame))
        candidatos = indice.get(("nome", nome), []) if nome else []
    data_solicitacao = solicitacao.created_at.date() if solicitacao.created_at else None

    for row in candidatos:
        data_realizacao = valor_para_data(row.get("DATA_EXAME"))
        if data_solicitacao and data_realizacao and data_realizacao < data_solicitacao:
            continue
        if paciente_compativel(row, atendimento, spdata):
            return row

    return None


def status_solicitacao(solicitacao, realizacao, hoje=None):
    if realizacao:
        return "realizado"

    hoje = hoje or date.today()
    data_solicitacao = solicitacao.created_at.date() if solicitacao.created_at else hoje
    if hoje - data_solicitacao >= PRAZO_NAO_CONVERTIDO:
        return "nao-convertido"

    return "pendente"


def solicitacao_para_item(solicitacao, atendimento, exame, spdata, convenio, realizacao, hoje=None):
    hoje = hoje or date.today()
    data_solicitacao = solicitacao.created_at.date() if solicitacao.created_at else None
    status = status_solicitacao(solicitacao, realizacao, hoje)
    valor_estimado = numero(realizacao.get("VALOR_ESTIMADO")) if realizacao else 0
    codigo_tuss = ""
    codigo_exame_local = codigo_exame(exame)
    codigo_exame_spdata = texto(realizacao.get("EXAME")) if realizacao else ""

    if realizacao:
        codigo_tuss = texto(realizacao.get("CODAMB_CONVENIO")) or texto(realizacao.get("CODAMB_PROCEDIMENTO"))

    if not codigo_tuss and exame:
        codigo_tuss = texto(exame.codigo_amb)
        if codigo_tuss == "0":
            codigo_tuss = ""

    return {
        "id": solicitacao.id,
        "clinicaId": getattr(atendimento, "unidade_id", None) or getattr(spdata, "unidade_id", None),
        "unidadeId": getattr(atendimento, "unidade_id", None) or getattr(spdata, "unidade_id", None),
        "localSolicitacaoId": solicitacao.id,
        "spdataExameId": realizacao.get("ID_EXAME_LANCAMENTO") if realizacao else None,
        "spdataContaId": realizacao.get("ID_SICADATE") if realizacao else None,
        "spdataAtendimentoId": atendimento.spdata_atendimento_id,
        "paciente": texto(atendimento.paciente_nome) or texto(getattr(spdata, "paciente", None)) or "Paciente não informado",
        "cpf": cpf_normalizado(atendimento.paciente_cpf, getattr(spdata, "cpf", None)),
        "prontuario": texto(getattr(spdata, "prontuario", None)),
        "convenio": texto(getattr(convenio, "nome", None)) or texto(getattr(spdata, "id_convenio_spdata", None)),
        "medico": texto(getattr(spdata, "medico", None)) or "Médico não informado",
        "crm": texto(getattr(spdata, "crm_medico", None)),
        "especialidade": "Especialidade não informada",
        "exame": texto(getattr(exame, "nome", None)) or texto(solicitacao.tipo_exame),
        "codigoTuss": codigo_tuss or codigo_exame_local or codigo_exame_spdata,
        "codigoExame": codigo_exame_local or codigo_exame_spdata,
        "dataSolicitacao": data_iso(data_solicitacao),
        "dataRealizacao": data_iso(realizacao.get("DATA_EXAME")) if realizacao else None,
        "diasEmAberto": dias_desde(data_solicitacao, hoje),
        "status": status,
        "statusSpdata": texto(realizacao.get("STATUS_EXAME")) if realizacao else "",
        "valorEstimado": valor_estimado,
        "valorRealizado": valor_estimado if status == "realizado" else None,
        "ultimoContato": None,
        "responsavel": None,
        "telefone": texto(getattr(spdata, "celular", None)) or texto(getattr(spdata, "telefone", None)),
        "guia": "",
        "senha": "",
        "dataColeta": data_iso(realizacao.get("COLETA") or realizacao.get("PREVISAOCOLETA")) if realizacao else "",
        "dataLiberacao": data_iso(realizacao.get("DATA_HORA_LIBERA_EXAME") or realizacao.get("DTEMIRES")) if realizacao else "",
        "pendencia": "" if exame or realizacao else "Solicitação local sem vínculo com catálogo de exames.",
    }


def listar_retencao_exames(data_ini, data_fim, unidade=None):
    registros_locais = buscar_solicitacoes_locais(data_ini, data_fim, unidade=unidade)
    realizacoes = buscar_realizacoes_spdata(registros_locais, unidade=unidade)
    indice = indexar_realizacoes(realizacoes)
    hoje = date.today()

    items = [
        solicitacao_para_item(
            solicitacao,
            atendimento,
            exame,
            spdata,
            convenio,
            encontrar_realizacao(solicitacao, atendimento, exame, spdata, indice),
            hoje,
        )
        for solicitacao, atendimento, exame, spdata, convenio in registros_locais
    ]

    return {
        "items": items,
        "dataIni": data_ini.isoformat(),
        "dataFim": data_fim.isoformat(),
    }
