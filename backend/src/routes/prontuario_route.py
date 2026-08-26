import json
import re
from datetime import date, datetime, time, timedelta

from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from src.security.decorators import roles_required
from src.models.auditoria_model import AcaoAuditoria
from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.db.handler_sql_server import ConnectionSqlServer
from src.models.db.handler_redis_db import ConnectionDBRedis
from src.services.auditoria_service import registrar_auditoria
from src.settings.extensions import db
from src.models.atendimentos_model import Atendimento
from src.models.anamnese_model import Anamnese
from src.models.diagnostico_model import Diagnostico
from src.models.prescricao_model import Prescricao
from src.models.solicitacao_exame_model import SolicitacaoExame
from src.models.evolucoes_medicas_model import EvolucaoMedica
from src.models.unidade_model import Unidade
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.services.spdata_atendimentos_service import get_crm_medico_usuario
from src.security.unidades import unidade_id_request
from src.services.unidades_service import resolver_unidade_usuario
from src.utils.normalizar import normalizar_cpf


prontuario_bp = Blueprint("prontuario", __name__, url_prefix="/prontuario")

CID_CACHE_TTL = 3600
CID_CODE_PATTERN = re.compile(r"^[A-Za-z][0-9.]*$")
SPDATA_ANAMNESE_MODELO_COD = "MED26"
SPDATA_ANAMNESE_PERGUNTA_IDS = (2171, 2172, 2173, 2174, 2176, 2780)
RTF_DESTINATIONS = {
    "fonttbl", "colortbl", "datastore", "themedata", "stylesheet", "info",
    "pict", "object", "header", "footer", "generator", "xmlnstbl",
}
RTF_SYMBOLS = {
    "par": "\n",
    "line": "\n",
    "tab": "\t",
    "emdash": "—",
    "endash": "–",
    "bullet": "•",
    "lquote": "‘",
    "rquote": "’",
    "ldblquote": "“",
    "rdblquote": "”",
}


def _solicitacao_exame_to_dict(solicitacao):
    exame = solicitacao.exame
    nome = exame.nome if exame else (solicitacao.descricao or solicitacao.tipo_exame)

    return {
        "nome": nome,
        "exame_id": solicitacao.exame_id,
        "descricao": solicitacao.descricao,
        "tipo_exame": solicitacao.tipo_exame,
        "orientacao": solicitacao.orientacao,
        "codigo_alfanumerico": exame.codigo_alfanumerico if exame else None,
        "codigo_amb": exame.codigo_amb if exame else None,
        "idTokenLancamentoExame": getattr(solicitacao, "id_token_lancamento_exame", None),
    }


def _somente_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _cpf_valido(valor):
    return normalizar_cpf(valor)


def _texto_ou_none(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    return texto or None


def _normalizar_prontuario(valor):
    texto = _texto_ou_none(valor)
    if not texto:
        return None

    if texto.endswith(".0") and texto[:-2].isdigit():
        return texto[:-2]

    return texto


def _int_ou_none(valor):
    if valor is None or valor == "":
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        texto = str(valor).strip()
        if not texto:
            return None
        try:
            return int(float(texto.replace(",", ".")))
        except (TypeError, ValueError):
            return None


def _normalizar_sql_value(valor):
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()

    if hasattr(valor, "read"):
        return _normalizar_sql_value(valor.read())

    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.decode("cp1252", errors="replace")

    return valor


def _mesmo_texto(valor_a, valor_b):
    texto_a = _texto_ou_none(valor_a)
    texto_b = _texto_ou_none(valor_b)
    if texto_a is None or texto_b is None:
        return False
    return texto_a.casefold() == texto_b.casefold()


def _referencia_paciente_valida(referencia, paciente_id=None, cpf=None, nome=None):
    validacoes = []
    if paciente_id:
        validacoes.append(referencia.get("paciente_id") == paciente_id)
    if cpf:
        validacoes.append(referencia.get("cpf") == cpf)
    if nome:
        validacoes.append(_mesmo_texto(referencia.get("nome"), nome))

    return not validacoes or any(validacoes)


def _unidade_por_centro_custo(codigo_centro_custo):
    codigo_centro_custo = _int_ou_none(codigo_centro_custo)
    if codigo_centro_custo is None:
        return None

    return db.session.execute(
        select(Unidade).where(
            Unidade.ativa.is_(True),
            Unidade.codigo_spdata_centro_custo == codigo_centro_custo,
        )
    ).scalars().first()


def _resolver_unidade_atendimento(usuario_id, unidade_id=None, centro_custo=None):
    if unidade_id:
        return resolver_unidade_usuario(usuario_id, unidade_id)

    unidade = _unidade_por_centro_custo(centro_custo)
    if unidade:
        return resolver_unidade_usuario(usuario_id, unidade.id)

    raise PermissionError("Usuário não possui acesso à unidade do atendimento")


def _normalizar_texto_linhas(texto):
    if texto is None:
        return None

    linhas = [linha.strip() for linha in str(texto).splitlines()]
    texto = "\n".join(linha for linha in linhas if linha)
    return texto or None


def _referencia_firebird_atendimento(
    spdata_atendimento_id,
    usuario_id,
    crm_medico,
    paciente_id=None,
    cpf=None,
    nome=None,
):
    spdata_atendimento_id = _int_ou_none(spdata_atendimento_id)
    if not spdata_atendimento_id:
        return None

    sql = """
        SELECT FIRST 1
            a.ID AS SPDATA_ATENDIMENTO_ID,
            a.ID_RICADPAC AS ID_PACIENTE_SPDATA,
            a.ID_TBCENCUS AS ID_CENTRO_CUSTO_SPDATA,
            paciente.PRONT AS PRONTUARIO,
            paciente.NOME AS PACIENTE,
            paciente.CPF AS CPF
        FROM ATCABECATEND a
        INNER JOIN RICADPAC paciente
            ON paciente.ID = a.ID_RICADPAC
        INNER JOIN TBCBOPRO tb
            ON a.ID_TBCBOPRO_ATENDIMENTO = tb.ID
        WHERE a.ID = ?
          AND CAST(tb.COD AS VARCHAR(50)) = CAST(? AS VARCHAR(50))
    """

    with ConnectionDBFireBird() as con:
        cursor = con.cursor()
        try:
            cursor.execute(
                sql,
                (
                    spdata_atendimento_id,
                    crm_medico,
                ),
            )
            row = cursor.fetchone()
            if not row:
                return None

            colunas = [desc[0].strip().upper() for desc in cursor.description]
            item = {
                coluna: _normalizar_sql_value(valor)
                for coluna, valor in zip(colunas, row)
            }
        finally:
            cursor.close()

    unidade_atendimento = _resolver_unidade_atendimento(
        usuario_id,
        centro_custo=item.get("ID_CENTRO_CUSTO_SPDATA"),
    )

    referencia = {
        "paciente_id": _int_ou_none(item.get("ID_PACIENTE_SPDATA")) or paciente_id,
        "cpf": _cpf_valido(item.get("CPF")) or cpf,
        "nome": _texto_ou_none(item.get("PACIENTE")) or nome,
        "prontuario": _normalizar_prontuario(item.get("PRONTUARIO")),
        "unidade_id": unidade_atendimento.id,
        "centro_custo": _int_ou_none(item.get("ID_CENTRO_CUSTO_SPDATA")),
    }

    if not _referencia_paciente_valida(referencia, paciente_id=paciente_id, cpf=cpf, nome=nome):
        return None

    return referencia


def _referencia_spdata_atendimento_local(
    usuario_id,
    crm_medico,
    spdata_atendimento_id,
    paciente_id=None,
    cpf=None,
    nome=None,
):
    spdata_atendimento_id = _int_ou_none(spdata_atendimento_id)
    if not spdata_atendimento_id:
        return None

    registro = db.session.execute(
        select(MedSpdataAtendimento)
        .where(MedSpdataAtendimento.spdata_atendimento_id == spdata_atendimento_id)
        .order_by(MedSpdataAtendimento.data_hora_entrada.desc())
    ).scalars().first()

    if not registro or not _mesmo_texto(registro.crm_medico, crm_medico):
        return None

    unidade_atendimento = _resolver_unidade_atendimento(
        usuario_id,
        unidade_id=registro.unidade_id,
        centro_custo=registro.id_centro_custo_spdata,
    )

    referencia = {
        "paciente_id": registro.id_paciente_spdata or paciente_id,
        "cpf": _cpf_valido(registro.cpf) or cpf,
        "nome": _texto_ou_none(registro.paciente) or nome,
        "prontuario": _normalizar_prontuario(registro.prontuario),
        "unidade_id": unidade_atendimento.id,
        "centro_custo": _int_ou_none(registro.id_centro_custo_spdata),
    }

    if not _referencia_paciente_valida(referencia, paciente_id=paciente_id, cpf=cpf, nome=nome):
        return None

    return referencia


def _referencia_autorizada_paciente(
    usuario_id,
    paciente_id=None,
    cpf=None,
    nome=None,
    spdata_atendimento_id=None,
    unidade_id=None,
):
    crm_medico = get_crm_medico_usuario(usuario_id)
    cpf = _cpf_valido(cpf)
    nome = _texto_ou_none(nome)

    if spdata_atendimento_id:
        referencia_spdata_atendimento = _referencia_spdata_atendimento_local(
            usuario_id,
            crm_medico,
            spdata_atendimento_id,
            paciente_id=paciente_id,
            cpf=cpf,
            nome=nome,
        )
        if referencia_spdata_atendimento:
            return referencia_spdata_atendimento

        referencia_firebird = _referencia_firebird_atendimento(
            spdata_atendimento_id,
            usuario_id,
            crm_medico,
            paciente_id=paciente_id,
            cpf=cpf,
            nome=nome,
        )
        if referencia_firebird:
            return referencia_firebird

    unidade = resolver_unidade_usuario(usuario_id, unidade_id)
    filtros_unidade_agenda = [MedSpdataAgenda.unidade_id == unidade.id]
    if unidade.codigo_spdata_agenda:
        filtros_unidade_agenda.append(MedSpdataAgenda.codigo_unidade_spdata == unidade.codigo_spdata_agenda)

    filtros_spdata = []
    if spdata_atendimento_id:
        filtros_spdata.append(or_(
            MedSpdataAtendimento.id == spdata_atendimento_id,
            MedSpdataAtendimento.spdata_atendimento_id == spdata_atendimento_id,
        ))
    if paciente_id:
        filtros_spdata.append(MedSpdataAtendimento.id_paciente_spdata == paciente_id)
    if cpf:
        filtros_spdata.append(MedSpdataAtendimento.cpf == cpf)

    if filtros_spdata:
        registro = db.session.execute(
            select(MedSpdataAtendimento)
            .where(
                MedSpdataAtendimento.crm_medico == crm_medico,
                or_(
                    MedSpdataAtendimento.unidade_id == unidade.id,
                    MedSpdataAtendimento.id_centro_custo_spdata == unidade.codigo_spdata_centro_custo,
                ),
                or_(*filtros_spdata),
            )
            .order_by(MedSpdataAtendimento.data_hora_entrada.desc())
        ).scalars().first()
        if registro:
            return {
                "paciente_id": registro.id_paciente_spdata or paciente_id,
                "cpf": _cpf_valido(registro.cpf) or cpf,
                "nome": _texto_ou_none(registro.paciente) or nome,
                "prontuario": _normalizar_prontuario(registro.prontuario),
            }

    filtros_agenda = []
    if paciente_id:
        filtros_agenda.append(MedSpdataAgenda.id_paciente_spdata == paciente_id)
    if cpf:
        filtros_agenda.append(MedSpdataAgenda.cpf == cpf)

    if filtros_agenda:
        agenda = db.session.execute(
            select(MedSpdataAgenda)
            .where(
                or_(
                    MedSpdataAgenda.crm_atend == crm_medico,
                    MedSpdataAgenda.crm == crm_medico,
                ),
                or_(*filtros_unidade_agenda),
                or_(*filtros_agenda),
            )
            .order_by(MedSpdataAgenda.data_agenda.desc())
        ).scalars().first()
        if agenda:
            return {
                "paciente_id": agenda.id_paciente_spdata or paciente_id,
                "cpf": _cpf_valido(agenda.cpf) or cpf,
                "nome": _texto_ou_none(agenda.paciente) or nome,
                "prontuario": _normalizar_prontuario(agenda.prontuario),
            }

    filtros_local = []
    if spdata_atendimento_id:
        filtros_local.append(Atendimento.spdata_atendimento_id == spdata_atendimento_id)
    if paciente_id:
        filtros_local.append(Atendimento.spdata_paciente_id == paciente_id)
    if cpf:
        filtros_local.append(Atendimento.paciente_cpf == cpf)

    if filtros_local:
        atendimento = db.session.execute(
            select(Atendimento)
            .join(EvolucaoMedica, EvolucaoMedica.atendimento_id == Atendimento.id)
            .where(
                EvolucaoMedica.medico_id == usuario_id,
                or_(
                    Atendimento.unidade_id == unidade.id,
                    Atendimento.unidade_id.is_(None),
                ),
                or_(*filtros_local),
            )
            .order_by(Atendimento.data_atendimento.desc())
        ).scalars().first()
        if atendimento:
            return {
                "paciente_id": atendimento.spdata_paciente_id or paciente_id,
                "cpf": _cpf_valido(atendimento.paciente_cpf) or cpf,
                "nome": _texto_ou_none(atendimento.paciente_nome) or nome,
                "prontuario": None,
            }

    raise PermissionError("Paciente não encontrado")


def _decode_rtf_hex(valor):
    try:
        return bytes.fromhex(valor).decode("cp1252")
    except (ValueError, UnicodeDecodeError):
        return ""


def _rtf_para_texto(valor):
    texto = _texto_ou_none(valor)
    if not texto:
        return None

    if texto.startswith('"') and texto.endswith('"'):
        texto = texto[1:-1].strip()

    if not texto.lstrip().startswith("{\\rtf"):
        return _normalizar_texto_linhas(texto)

    resultado = []
    stack = []
    ignorable = False
    ucskip = 1
    curskip = 0
    i = 0

    while i < len(texto):
        char = texto[i]

        if char == "{":
            stack.append((ucskip, ignorable))
            i += 1
            continue

        if char == "}":
            if stack:
                ucskip, ignorable = stack.pop()
            i += 1
            continue

        if char == "\\":
            i += 1
            if i >= len(texto):
                break

            marcador = texto[i]
            if marcador in "{}\\":
                if not ignorable and curskip == 0:
                    resultado.append(marcador)
                elif curskip > 0:
                    curskip -= 1
                i += 1
                continue

            if marcador == "'" and i + 2 < len(texto):
                if not ignorable and curskip == 0:
                    resultado.append(_decode_rtf_hex(texto[i + 1:i + 3]))
                elif curskip > 0:
                    curskip -= 1
                i += 3
                continue

            if marcador == "*":
                ignorable = True
                i += 1
                continue

            if not marcador.isalpha():
                if not ignorable and marcador == "~":
                    resultado.append(" ")
                i += 1
                continue

            inicio = i
            while i < len(texto) and texto[i].isalpha():
                i += 1
            palavra = texto[inicio:i]

            sinal = 1
            if i < len(texto) and texto[i] == "-":
                sinal = -1
                i += 1

            numero_inicio = i
            while i < len(texto) and texto[i].isdigit():
                i += 1
            numero = texto[numero_inicio:i]
            argumento = sinal * int(numero) if numero else None

            if i < len(texto) and texto[i] == " ":
                i += 1

            if palavra in RTF_DESTINATIONS:
                ignorable = True
                continue

            if ignorable:
                continue

            if palavra == "uc" and argumento is not None:
                ucskip = argumento
                continue

            if palavra == "u" and argumento is not None:
                codigo = argumento if argumento >= 0 else argumento + 65536
                try:
                    resultado.append(chr(codigo))
                except ValueError:
                    pass
                curskip = ucskip
                continue

            simbolo = RTF_SYMBOLS.get(palavra)
            if simbolo is not None:
                resultado.append(simbolo)
                continue

            continue

        if not ignorable:
            if curskip > 0:
                curskip -= 1
            else:
                resultado.append(char)

        i += 1

    return _normalizar_texto_linhas("".join(resultado))


def _referencia_paciente_biodata(paciente_id, usuario_id):
    spdata_atendimento_id = (
        request.args.get("spdataAtendimentoId", type=int)
        or request.args.get("spdata_atendimento_id", type=int)
    )
    referencia = _referencia_autorizada_paciente(
        usuario_id,
        paciente_id=paciente_id,
        cpf=request.args.get("cpf"),
        nome=request.args.get("nome"),
        spdata_atendimento_id=spdata_atendimento_id,
        unidade_id=unidade_id_request(),
    )
    return referencia["cpf"], referencia["nome"]


def _executar_historico_biodata(where_clause, params, limit, offset):
    row_start = offset + 1
    row_end = offset + limit + 1
    sql = f"""
        WITH historico AS (
            SELECT
                an.intAnamneseId AS ID_ANAMNESE,
                an.datAnamnese AS DATA_ANAMNESE,
                CAST(an.strAnamnese AS NVARCHAR(MAX)) AS ANAMNESE_RTF,
                CAST(an.strAnamneseMobile AS NVARCHAR(MAX)) AS ANAMNESE_MOBILE,
                c.intClienteId AS ID_PACIENTE_BIODATA,
                c.strCliente AS PACIENTE,
                c.strCPF AS CPF,
                p.strProfissional AS MEDICO,
                ROW_NUMBER() OVER (
                    ORDER BY an.datAnamnese DESC, an.intAnamneseId DESC
                ) AS RN
            FROM [BioData].[dbo].[tblAnamnese] an
            JOIN [Repositorio].[dbo].[tblCliente] c
                ON c.intClienteId = an.intClienteId
            LEFT JOIN [BioData].[dbo].[tblProfissional] p
                ON p.intProfissionalId = an.intProfissionalId
            WHERE {where_clause}
        )
        SELECT
            ID_ANAMNESE,
            DATA_ANAMNESE,
            ANAMNESE_RTF,
            ANAMNESE_MOBILE,
            ID_PACIENTE_BIODATA,
            PACIENTE,
            CPF,
            MEDICO
        FROM historico
        WHERE RN BETWEEN ? AND ?
        ORDER BY RN;
    """

    with ConnectionSqlServer() as con:
        cursor = con.cursor()
        cursor.execute(sql, [*params, row_start, row_end])
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()

    items = [
        {
            coluna: _normalizar_sql_value(valor)
            for coluna, valor in zip(columns, row)
        }
        for row in rows
    ]
    return items[:limit], len(items) > limit


def _historico_biodata(paciente_id, usuario_id, limit=10, offset=0):
    cpf, nome = _referencia_paciente_biodata(paciente_id, usuario_id)
    historico = []
    has_more = False

    if cpf:
        historico, has_more = _executar_historico_biodata(
            "c.strCPF = ?",
            [cpf],
            limit,
            offset,
        )

    if not historico and nome and (not cpf or offset == 0):
        historico, has_more = _executar_historico_biodata(
            "UPPER(LTRIM(RTRIM(c.strCliente))) = UPPER(LTRIM(RTRIM(?)))",
            [nome],
            limit,
            offset,
        )

    result = []
    for item in historico:
        anamnese = _rtf_para_texto(item.get("ANAMNESE_RTF")) or _rtf_para_texto(item.get("ANAMNESE_MOBILE"))
        result.append({
            "ORIGEM": "BIODATA",
            "ID_ATENDIMENTO": None,
            "ID_ANAMNESE": str(item.get("ID_ANAMNESE")) if item.get("ID_ANAMNESE") is not None else None,
            "ID_PACIENTE": item.get("ID_PACIENTE_BIODATA") or paciente_id,
            "PACIENTE": item.get("PACIENTE") or nome,
            "DATA_CONSULTA": item.get("DATA_ANAMNESE"),
            "DATA_ENCERRAMENTO": None,
            "DATA_ANAMNESE": item.get("DATA_ANAMNESE"),
            "MEDICO": item.get("MEDICO"),
            "ANAMNESE": anamnese,
            "OBS_ATENDIMENTO": None,
            "QUEIXA_PRINCIPAL": None,
            "CID_PRINCIPAL": None,
            "DIAGNOSTICO_PRINCIPAL": None,
            "CID_SECUNDARIO": None,
            "DIAGNOSTICO_SECUNDARIO": None,
            "ID_EVOLUCAO": None,
            "ID_SOLICITACAO_EXAME": None,
        })

    return {
        "items": result,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }


def _identificadores_referencia(referencia, spdata_atendimento_id=None):
    filtros_spdata = []
    filtros_agenda = []

    paciente_id = referencia.get("paciente_id")
    cpf = referencia.get("cpf")
    nome = referencia.get("nome")

    if spdata_atendimento_id:
        filtros_spdata.append(or_(
            MedSpdataAtendimento.id == spdata_atendimento_id,
            MedSpdataAtendimento.spdata_atendimento_id == spdata_atendimento_id,
        ))
    if paciente_id:
        filtros_spdata.append(MedSpdataAtendimento.id_paciente_spdata == paciente_id)
        filtros_agenda.append(MedSpdataAgenda.id_paciente_spdata == paciente_id)
    if cpf:
        filtros_spdata.append(MedSpdataAtendimento.cpf == cpf)
        filtros_agenda.append(MedSpdataAgenda.cpf == cpf)
    if nome:
        filtros_spdata.append(MedSpdataAtendimento.paciente.ilike(nome))
        filtros_agenda.append(MedSpdataAgenda.paciente.ilike(nome))

    return filtros_spdata, filtros_agenda


def _prontuario_local_referencia(referencia, usuario_id, spdata_atendimento_id=None, unidade_id=None):
    prontuario = _normalizar_prontuario(referencia.get("prontuario"))
    if prontuario:
        return prontuario

    unidade = resolver_unidade_usuario(usuario_id, unidade_id)
    filtros_spdata, filtros_agenda = _identificadores_referencia(
        referencia,
        spdata_atendimento_id=spdata_atendimento_id,
    )

    if filtros_spdata:
        registro = db.session.execute(
            select(MedSpdataAtendimento.prontuario)
            .where(
                or_(
                    MedSpdataAtendimento.unidade_id == unidade.id,
                    MedSpdataAtendimento.id_centro_custo_spdata == unidade.codigo_spdata_centro_custo,
                ),
                MedSpdataAtendimento.prontuario.is_not(None),
                MedSpdataAtendimento.prontuario != "",
                or_(*filtros_spdata),
            )
            .order_by(MedSpdataAtendimento.data_hora_entrada.desc())
        ).scalars().first()
        prontuario = _normalizar_prontuario(registro)
        if prontuario:
            return prontuario

    if filtros_agenda:
        filtros_unidade_agenda = [MedSpdataAgenda.unidade_id == unidade.id]
        if unidade.codigo_spdata_agenda:
            filtros_unidade_agenda.append(MedSpdataAgenda.codigo_unidade_spdata == unidade.codigo_spdata_agenda)

        agenda = db.session.execute(
            select(MedSpdataAgenda.prontuario)
            .where(
                or_(*filtros_unidade_agenda),
                MedSpdataAgenda.prontuario.is_not(None),
                MedSpdataAgenda.prontuario != "",
                or_(*filtros_agenda),
            )
            .order_by(MedSpdataAgenda.data_agenda.desc())
        ).scalars().first()
        prontuario = _normalizar_prontuario(agenda)
        if prontuario:
            return prontuario

    return None


def _prontuario_firebird_referencia(referencia):
    consultas = []
    paciente_id = referencia.get("paciente_id")
    cpf = referencia.get("cpf")
    nome = referencia.get("nome")

    if paciente_id:
        consultas.append(("RP.ID = ?", [paciente_id]))
    if cpf:
        consultas.append(("RP.CPF = ?", [cpf]))
    if nome:
        consultas.append(("UPPER(TRIM(RP.NOME)) = UPPER(TRIM(?))", [nome]))

    if not consultas:
        return None

    with ConnectionDBFireBird() as con:
        cursor = con.cursor()
        try:
            for where_clause, params in consultas:
                cursor.execute(
                    f"""
                    SELECT FIRST 1
                        RP.PRONT AS PRONTUARIO
                    FROM RICADPAC RP
                    WHERE {where_clause}
                      AND RP.PRONT IS NOT NULL
                    ORDER BY RP.ID DESC
                    """,
                    params,
                )
                row = cursor.fetchone()
                if row:
                    prontuario = _normalizar_prontuario(_normalizar_sql_value(row[0]))
                    if prontuario:
                        return prontuario
        finally:
            cursor.close()

    return None


def _prontuario_spdata_referencia(referencia, usuario_id, spdata_atendimento_id=None, unidade_id=None):
    unidade_referencia_id = referencia.get("unidade_id") or unidade_id
    return (
        _prontuario_local_referencia(
            referencia,
            usuario_id,
            spdata_atendimento_id=spdata_atendimento_id,
            unidade_id=unidade_referencia_id,
        )
        or _prontuario_firebird_referencia(referencia)
    )


def _linha_anamnese_spdata(pergunta, resposta):
    pergunta = _normalizar_texto_linhas(pergunta)
    resposta = _rtf_para_texto(resposta) or _normalizar_texto_linhas(resposta)

    if not resposta:
        return None
    if pergunta:
        return f"{pergunta}: {resposta}"
    return resposta


def _montar_anamnese_spdata(respostas):
    linhas = []
    for resposta in respostas:
        linha = _linha_anamnese_spdata(
            resposta.get("PERGUNTA"),
            resposta.get("RESPOSTA"),
        )
        if linha:
            linhas.append(linha)

    return "\n".join(linhas) or None


def _executar_historico_spdata(prontuario, limit, offset):
    evolucoes_sql = f"""
        SELECT FIRST {limit + 1} SKIP {offset}
            RP.ID AS ID_PACIENTE_SPDATA,
            RP.PRONT AS PRONTUARIO,
            RP.NOME AS PACIENTE,
            PC.ID_CABEVOL,
            PC.ID_HTATENDIMENTO,
            PC.DATA_HORA_EVOLUCAO,
            PC.ID_EVOLUCAO,
            PE.DESCRICAO AS MODELO_EVOLUCAO
        FROM RICADPAC RP
        INNER JOIN HTPACIENTE HP
            ON HP.ID_RICADPAC = RP.ID
        INNER JOIN PRCABEVOL PC
            ON PC.ID_HTPACIENTE = HP.ID
        INNER JOIN PREVOLUCAO PE
            ON PE.ID_EVOLUCAO = PC.ID_EVOLUCAO
        WHERE RP.PRONT = ?
          AND PE.COD = ?
        ORDER BY
            PC.DATA_HORA_EVOLUCAO DESC,
            PC.ID_CABEVOL DESC
    """

    pergunta_ids_sql = ", ".join(str(id_pergunta) for id_pergunta in SPDATA_ANAMNESE_PERGUNTA_IDS)

    with ConnectionDBFireBird() as con:
        cursor = con.cursor()
        try:
            cursor.execute(evolucoes_sql, [prontuario, SPDATA_ANAMNESE_MODELO_COD])
            colunas_evolucoes = [desc[0].strip().upper() for desc in cursor.description]
            evolucoes = [
                {
                    coluna: _normalizar_sql_value(valor)
                    for coluna, valor in zip(colunas_evolucoes, row)
                }
                for row in cursor.fetchall()
            ]

            has_more = len(evolucoes) > limit
            evolucoes = evolucoes[:limit]
            ids_cabevol = [evolucao.get("ID_CABEVOL") for evolucao in evolucoes if evolucao.get("ID_CABEVOL") is not None]

            if not ids_cabevol:
                return [], has_more

            placeholders = ", ".join("?" for _ in ids_cabevol)
            respostas_sql = f"""
                SELECT
                    PV.ID_CABEVOL,
                    PP.ID AS ID_PERGUNTA,
                    PP.DESCRICAO AS PERGUNTA,
                    PV.CONTEVOL AS RESPOSTA
                FROM PREVOLPAC PV
                INNER JOIN PRRESPOSTA PR
                    ON PR.ID_RESPOSTA = PV.ID_RESPOSTA
                INNER JOIN PRPERGUNTA PP
                    ON PP.ID = PR.ID_PRPERGUNTA
                WHERE PV.ID_CABEVOL IN ({placeholders})
                  AND PP.ID IN ({pergunta_ids_sql})
                ORDER BY
                    PV.ID_CABEVOL,
                    PP.ID
            """
            cursor.execute(respostas_sql, ids_cabevol)
            colunas_respostas = [desc[0].strip().upper() for desc in cursor.description]
            respostas = [
                {
                    coluna: _normalizar_sql_value(valor)
                    for coluna, valor in zip(colunas_respostas, row)
                }
                for row in cursor.fetchall()
            ]
        finally:
            cursor.close()

    respostas_por_evolucao = {str(id_cabevol): [] for id_cabevol in ids_cabevol}
    for resposta in respostas:
        id_cabevol = resposta.get("ID_CABEVOL")
        respostas_por_evolucao.setdefault(str(id_cabevol), []).append(resposta)

    result = []
    for evolucao in evolucoes:
        id_cabevol = evolucao.get("ID_CABEVOL")
        data_evolucao = evolucao.get("DATA_HORA_EVOLUCAO")
        anamnese = _montar_anamnese_spdata(respostas_por_evolucao.get(str(id_cabevol), []))
        result.append({
            "ORIGEM": "SPDATA",
            "ID_ATENDIMENTO": str(evolucao.get("ID_HTATENDIMENTO")) if evolucao.get("ID_HTATENDIMENTO") is not None else None,
            "ID_ANAMNESE": f"SPDATA-{id_cabevol}" if id_cabevol is not None else None,
            "ID_PACIENTE": evolucao.get("ID_PACIENTE_SPDATA"),
            "PACIENTE": evolucao.get("PACIENTE"),
            "DATA_CONSULTA": data_evolucao,
            "DATA_ENCERRAMENTO": None,
            "DATA_ANAMNESE": data_evolucao,
            "MEDICO": None,
            "MODELO_EVOLUCAO": evolucao.get("MODELO_EVOLUCAO"),
            "ANAMNESE": anamnese,
            "OBS_ATENDIMENTO": None,
            "QUEIXA_PRINCIPAL": None,
            "CID_PRINCIPAL": None,
            "DIAGNOSTICO_PRINCIPAL": None,
            "CID_SECUNDARIO": None,
            "DIAGNOSTICO_SECUNDARIO": None,
            "ID_EVOLUCAO": str(evolucao.get("ID_EVOLUCAO")) if evolucao.get("ID_EVOLUCAO") is not None else None,
            "ID_SOLICITACAO_EXAME": None,
        })

    return result, has_more


def _historico_spdata(paciente_id, usuario_id, limit=10, offset=0):
    spdata_atendimento_id = (
        request.args.get("spdataAtendimentoId", type=int)
        or request.args.get("spdata_atendimento_id", type=int)
    )
    unidade_id = unidade_id_request()
    referencia = _referencia_autorizada_paciente(
        usuario_id,
        paciente_id=paciente_id,
        cpf=request.args.get("cpf"),
        nome=request.args.get("nome"),
        spdata_atendimento_id=spdata_atendimento_id,
        unidade_id=unidade_id,
    )
    prontuario = _prontuario_spdata_referencia(
        referencia,
        usuario_id,
        spdata_atendimento_id=spdata_atendimento_id,
        unidade_id=unidade_id,
    )

    if not prontuario:
        return {
            "items": [],
            "limit": limit,
            "offset": offset,
            "has_more": False,
        }

    items, has_more = _executar_historico_spdata(prontuario, limit, offset)
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }

@prontuario_bp.route("/doenca-cid", methods=["GET"])
@jwt_required()
@roles_required("medico")
def doenca_cid():
    try:
        q = (request.args.get("q") or "").strip()

        limit = request.args.get("limit", default=20, type=int)
        offset = request.args.get("offset", default=0, type=int)

        limit = min(max(limit or 20, 1), 50)
        offset = max(offset or 0, 0)

        if not q:
            return jsonify({
                "items": [],
                "limit": limit,
                "offset": offset,
                "has_more": False
            }), 200

        is_codigo_cid = bool(CID_CODE_PATTERN.fullmatch(q))

        if (is_codigo_cid and len(q) < 2) or (not is_codigo_cid and len(q) < 3):
            return jsonify({
                "items": [],
                "limit": limit,
                "offset": offset,
                "has_more": False
            }), 200

        cache_key = f"prontuario:cid:{'codigo' if is_codigo_cid else 'nome'}:{q.casefold()}:{limit}:{offset}"
        redis_connection = ConnectionDBRedis()

        cached = redis_connection.get_cache(cache_key)
        if cached is not None:
            return jsonify(json.loads(cached)), 200

        row_start = offset + 1
        row_end = offset + limit

        where = [
            "COD IS NOT NULL",
            "NOME IS NOT NULL"
        ]
        params = []

        if is_codigo_cid:
            where.append("COD STARTING WITH ?")
            params.append(q.upper())
        else:
            where.append("NOME CONTAINING ?")
            params.append(q)

        sql = f"""
            SELECT
                COD AS CID,
                NOME AS DOENCA
            FROM TBCID10
            WHERE {' AND '.join(where)}
            ORDER BY COD
            ROWS {row_start} TO {row_end};
        """

        with ConnectionDBFireBird() as con:
            cursor = con.cursor()
            cursor.execute(sql, params)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]

        response = {
            "items": result,
            "limit": limit,
            "offset": offset,
            "has_more": len(result) == limit
        }

        redis_connection.set_cache(
            cache_key,
            json.dumps(response, default=str),
            ttl=CID_CACHE_TTL
        )

        return jsonify(response), 200

    except Exception:
        current_app.logger.exception("Erro ao buscar CID")
        return jsonify({"error": "Erro interno ao buscar CID"}), 500


@prontuario_bp.route("/historico-local/<int:paciente_id>")
@jwt_required()
@roles_required("medico")
def historico_paciente_local(paciente_id):
    # Busca no banco LOCAL os atendimentos finalizados deste paciente,
    # incluindo dados completos de anamnese, CIDs, medicamentos e exames.
    try:
        usuario_id = int(get_jwt_identity())
        spdata_atendimento_id = (
            request.args.get("spdataAtendimentoId", type=int)
            or request.args.get("spdata_atendimento_id", type=int)
        )
        referencia = _referencia_autorizada_paciente(
            usuario_id,
            paciente_id=paciente_id,
            cpf=request.args.get("cpf"),
            nome=request.args.get("nome"),
            spdata_atendimento_id=spdata_atendimento_id,
            unidade_id=unidade_id_request(),
        )
        paciente_id_autorizado = referencia.get("paciente_id")
        cpf = referencia["cpf"]
        nome = referencia["nome"]
        data = request.args.get("data")
        data_ref = None

        if data:
            try:
                data_ref = datetime.fromisoformat(str(data)[:10]).date()
            except ValueError:
                return jsonify({"error": "Data inválida"}), 400

        identificadores = []
        if paciente_id_autorizado:
            identificadores.append(Atendimento.spdata_paciente_id == paciente_id_autorizado)
        if cpf:
            identificadores.append(Atendimento.paciente_cpf == cpf)
        if nome:
            identificadores.append(Atendimento.paciente_nome.ilike(nome))

        if not identificadores:
            return jsonify([]), 200

        filtros = [
            Atendimento.status == "finalizado",
            or_(*identificadores),
        ]
        if data_ref:
            inicio = datetime.combine(data_ref, time.min)
            fim = datetime.combine(data_ref + timedelta(days=1), time.min)
            filtros.extend([
                Atendimento.data_atendimento >= inicio,
                Atendimento.data_atendimento < fim,
            ])

        atendimentos = db.session.execute(
            select(Atendimento)
            .options(
                selectinload(Atendimento.anamnese),
                selectinload(Atendimento.diagnosticos),
                selectinload(Atendimento.prescricoes),
                selectinload(Atendimento.solicitacoes_exames).selectinload(SolicitacaoExame.exame),
                selectinload(Atendimento.evolucoes_medicas).selectinload(EvolucaoMedica.medico),
            )
            .where(*filtros)
            .order_by(Atendimento.data_atendimento.desc())
        ).scalars().all()

        result = []
        for a in atendimentos:
            # Separa CID principal dos secundários
            diag_principal = next((d for d in a.diagnosticos if d.principal), None)
            diag_secundarios = [d for d in a.diagnosticos if not d.principal]

            # Busca nome do médico na primeira evolução registrada
            medico_nome = None
            if a.evolucoes_medicas:
                evol = a.evolucoes_medicas[0]
                if evol.medico:
                    medico_nome = evol.medico.nome_completo

            result.append({
                "spdata_atendimento_id": a.spdata_atendimento_id,
                "data_consulta": a.data_atendimento.isoformat() if a.data_atendimento else None,
                "medico_nome": medico_nome,
                "anamnese": a.anamnese.observacoes if a.anamnese else None,
                "cid_principal": diag_principal.cid_codigo if diag_principal else None,
                "cid_principal_descricao": diag_principal.cid_descricao if diag_principal else None,
                "cids_secundarios": [
                    {"codigo": d.cid_codigo, "descricao": d.cid_descricao}
                    for d in diag_secundarios
                ],
                "medicamentos": [
                    f"{p.medicamento} — {p.dosagem}" if p.dosagem else p.medicamento
                    for p in a.prescricoes
                ],
                "exames": [
                    _solicitacao_exame_to_dict(s)
                    for s in a.solicitacoes_exames
                ],
            })

        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_PRONTUARIO,
            entidade="paciente",
            entidade_id=paciente_id,
            usuario_id=usuario_id,
            descricao=f"Acesso ao histórico local do paciente. total={len(result)}",
        )

        return jsonify(result), 200

    except PermissionError:
        return jsonify({"error": "Paciente não encontrado"}), 404
    except Exception:
        current_app.logger.exception("Erro ao buscar histórico local do paciente")
        return jsonify({"error": "Erro interno ao buscar histórico local"}), 500


@prontuario_bp.route("/historico-paciente/<int:id>")
@jwt_required()
@roles_required("medico")
def historico_paciente(id:int):
    try:
        usuario_id = int(get_jwt_identity())
        limit = request.args.get("limit", default=10, type=int)
        offset = request.args.get("offset", default=0, type=int)

        limit = min(max(limit or 10, 1), 50)
        offset = max(offset or 0, 0)

        resultado = _historico_biodata(id, usuario_id, limit, offset)
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_HISTORICO_BIODATA,
            entidade="paciente",
            entidade_id=id,
            usuario_id=usuario_id,
            descricao=f"Acesso ao histórico BioData do paciente. limit={limit} offset={offset}",
        )

        return jsonify(resultado), 200

    except PermissionError:
        return jsonify({"error": "Paciente não encontrado"}), 404
    except Exception:
        current_app.logger.exception("Erro ao buscar histórico do paciente no BioData")
        return jsonify({"error": "Erro interno ao buscar histórico BioData"}), 500


@prontuario_bp.route("/historico-spdata/<int:id>")
@jwt_required()
@roles_required("medico")
def historico_paciente_spdata(id:int):
    try:
        usuario_id = int(get_jwt_identity())
        limit = request.args.get("limit", default=10, type=int)
        offset = request.args.get("offset", default=0, type=int)

        limit = min(max(limit or 10, 1), 50)
        offset = max(offset or 0, 0)

        resultado = _historico_spdata(id, usuario_id, limit, offset)
        registrar_auditoria(
            AcaoAuditoria.VISUALIZOU_HISTORICO_SPDATA,
            entidade="paciente",
            entidade_id=id,
            usuario_id=usuario_id,
            descricao=f"Acesso ao histórico SPDATA do paciente. limit={limit} offset={offset}",
        )

        return jsonify(resultado), 200

    except PermissionError:
        return jsonify({"error": "Paciente não encontrado"}), 404
    except Exception:
        current_app.logger.exception("Erro ao buscar histórico do paciente no SPDATA")
        return jsonify({"error": "Erro interno ao buscar histórico SPDATA"}), 500
