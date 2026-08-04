import json
import re
from datetime import date, datetime, time, timedelta

from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from src.security.decorators import roles_required
from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.db.handler_sql_server import ConnectionSqlServer
from src.models.db.handler_redis_db import ConnectionDBRedis
from src.settings.extensions import db
from src.models.atendimentos_model import Atendimento
from src.models.anamnese_model import Anamnese
from src.models.diagnostico_model import Diagnostico
from src.models.prescricao_model import Prescricao
from src.models.solicitacao_exame_model import SolicitacaoExame
from src.models.evolucoes_medicas_model import EvolucaoMedica
from src.models.model_mydsystem.med_spdata_atendimentos_model import MedSpdataAtendimento
from src.models.model_mydsystem.med_spdata_agenda_model import MedSpdataAgenda
from src.services.spdata_atendimentos_service import get_crm_medico_usuario
from src.security.unidades import unidade_id_request
from src.services.unidades_service import resolver_unidade_usuario
from src.utils.normalizar import normalizar_cpf


prontuario_bp = Blueprint("prontuario", __name__, url_prefix="/prontuario")

CID_CACHE_TTL = 3600
CID_CODE_PATTERN = re.compile(r"^[A-Za-z][0-9.]*$")
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


def _normalizar_sql_value(valor):
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()

    if isinstance(valor, bytes):
        try:
            return valor.decode("utf-8")
        except UnicodeDecodeError:
            return valor.decode("cp1252", errors="replace")

    return valor


def _normalizar_texto_linhas(texto):
    if texto is None:
        return None

    linhas = [linha.strip() for linha in str(texto).splitlines()]
    texto = "\n".join(linha for linha in linhas if linha)
    return texto or None


def _referencia_autorizada_paciente(
    usuario_id,
    paciente_id=None,
    cpf=None,
    nome=None,
    spdata_atendimento_id=None,
    unidade_id=None,
):
    crm_medico = get_crm_medico_usuario(usuario_id)
    unidade = resolver_unidade_usuario(usuario_id, unidade_id)
    filtros_unidade_agenda = [MedSpdataAgenda.unidade_id == unidade.id]
    if unidade.codigo_spdata_agenda:
        filtros_unidade_agenda.append(MedSpdataAgenda.codigo_unidade_spdata == unidade.codigo_spdata_agenda)
    cpf = _cpf_valido(cpf)
    nome = _texto_ou_none(nome)

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
                "cpf": _cpf_valido(registro.cpf) or cpf,
                "nome": _texto_ou_none(registro.paciente) or nome,
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
                "cpf": _cpf_valido(agenda.cpf) or cpf,
                "nome": _texto_ou_none(agenda.paciente) or nome,
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
                "cpf": _cpf_valido(atendimento.paciente_cpf) or cpf,
                "nome": _texto_ou_none(atendimento.paciente_nome) or nome,
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
    referencia = _referencia_autorizada_paciente(
        usuario_id,
        paciente_id=paciente_id,
        cpf=request.args.get("cpf"),
        nome=request.args.get("nome"),
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        if spdata_atendimento_id:
            identificadores.append(Atendimento.spdata_atendimento_id == spdata_atendimento_id)
        if paciente_id:
            identificadores.append(Atendimento.spdata_paciente_id == paciente_id)
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

        return jsonify(result), 200

    except PermissionError:
        return jsonify({"error": "Paciente não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

        return jsonify(_historico_biodata(id, usuario_id, limit, offset)), 200

    except PermissionError:
        return jsonify({"error": "Paciente não encontrado"}), 404
    except Exception as e:
        current_app.logger.exception("Erro ao buscar histórico do paciente no BioData")
        return jsonify({"error": str(e)}), 500
