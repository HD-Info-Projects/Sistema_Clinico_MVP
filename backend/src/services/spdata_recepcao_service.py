import os
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import String, cast, or_, select

from src.models.db.handler_fb_db import ConnectionDBFireBird
from src.models.medico_model import Medico
from src.models.model_mydsystem.med_procedimentos_model import Procedimento
from src.models.model_mydsystem.med_spdata_atendimentos_model import (
    MedSpdataAtendimento,
)
from src.models.model_mydsystem.med_spdata_convenios_model import MedSpdataConvenio
from src.models.usuario_model import Usuario
from src.models.usuario_unidade_model import UsuarioUnidade
from src.services.spdata_atendimentos_service import (
    _aplicar_atendimentos_spdata,
    _atendimentos_spdata_por_id,
    agenda_para_frontend,
    buscar_convenios_locais,
)
from src.services.unidades_service import resolver_unidade_usuario
from src.settings.extensions import db
from src.utils.normalizar import normalizar_cpf


IDENT_RE = re.compile(r"^[A-Z0-9_$]+$")


def normalizar_valor(valor):
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return int(valor) if valor == int(valor) else float(valor)
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    return valor


def normalizar_texto(valor, limite=None):
    if valor is None:
        return None

    texto = str(valor).strip()
    if limite:
        texto = texto[:limite]

    return texto or None


def normalizar_int(valor):
    if valor is None or valor == "":
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        texto = normalizar_texto(valor)
        if not texto:
            return None
        try:
            return int(float(texto.replace(",", ".")))
        except (TypeError, ValueError):
            return None


def normalizar_digitos(valor, tamanho=None):
    texto = normalizar_texto(valor)
    if not texto:
        return None

    digitos = re.sub(r"\D", "", texto)
    if not digitos:
        return None

    if tamanho:
        digitos = digitos[:tamanho]

    return digitos


def normalizar_digitos_int(valor, tamanho=None):
    digitos = normalizar_digitos(valor, tamanho)
    if not digitos:
        return None

    return int(digitos)


def normalizar_cpf_firebird(valor):
    cpf = normalizar_cpf(valor)
    return int(cpf) if cpf else None


def normalizar_cpf_frontend(valor):
    if valor is None or valor == "":
        return ""
    if isinstance(valor, (int, float, Decimal)):
        return str(int(valor)).zfill(11)

    texto = str(valor).strip()
    if re.fullmatch(r"\d+\.0+", texto):
        return str(int(float(texto))).zfill(11)

    return normalizar_cpf(texto) or ""


def normalizar_cep_firebird(valor):
    return normalizar_digitos_int(valor, 8)


def normalizar_cep_frontend(valor):
    cep = normalizar_digitos_int(valor, 8)
    if cep is None:
        return ""
    return str(cep).zfill(8)


def resolver_cep_spdata(cursor, valor):
    cep = normalizar_cep_firebird(valor)
    if cep is None:
        return None

    cursor.execute("SELECT FIRST 1 CEP FROM TBCEP WHERE CEP = ?", (cep,))
    row = cursor.fetchone()
    if row:
        return normalizar_int(row[0])

    return None


def resolver_ibge_spdata(cursor, valor):
    digitos = normalizar_digitos(valor)
    if not digitos:
        return None

    ibge = int(digitos)
    cursor.execute("SELECT FIRST 1 COD FROM TBMUIBGE WHERE COD = ?", (ibge,))
    row = cursor.fetchone()
    if row:
        return normalizar_int(row[0])

    if len(digitos) == 7:
        codigo_sem_digito = int(digitos[:6])
        digito = int(digitos[-1])
        cursor.execute(
            "SELECT FIRST 1 COD FROM TBMUIBGE WHERE COD = ? AND DIGITO = ?",
            (codigo_sem_digito, digito),
        )
        row = cursor.fetchone()
        if row:
            return normalizar_int(row[0])

    return None


def normalizar_referencias_paciente(cursor, valores):
    valores = dict(valores)
    if valores.get("CEP") is not None:
        valores["CEP"] = resolver_cep_spdata(cursor, valores["CEP"])
    if valores.get("IBGE") is not None:
        valores["IBGE"] = resolver_ibge_spdata(cursor, valores["IBGE"])
    return valores


def normalizar_tipo_atendimento(valor):
    tipo = normalizar_texto(valor, 1)
    tipo = tipo.upper() if tipo else None
    if tipo in ("E", "I"):
        return tipo
    return "E"


def normalizar_data(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return datetime.fromisoformat(str(valor)[:10]).date()


def normalizar_hora(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.time().replace(microsecond=0)
    if isinstance(valor, time):
        return valor.replace(microsecond=0)

    texto = str(valor).strip()
    if not texto:
        return None
    if texto.isdigit():
        texto = texto.zfill(4)
        return time(int(texto[:2]), int(texto[2:4]))
    if len(texto) == 5:
        return time.fromisoformat(texto)
    return time.fromisoformat(texto[:8])


def normalizar_datetime(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.replace(microsecond=0)
    return datetime.fromisoformat(str(valor).replace("T", " ")[:19])


def normalizar_data_validade(valor):
    texto = normalizar_texto(valor, 10)
    if not texto:
        return None

    if re.fullmatch(r"\d{2}/\d{4}", texto):
        mes, ano = texto.split("/")
        return date(int(ano), int(mes), 1)

    return normalizar_data(texto)


def normalizar_sexo(valor):
    texto = normalizar_texto(valor)
    if not texto:
        return None

    texto = texto.casefold()
    if texto.startswith("m"):
        return "M"
    if texto.startswith("f"):
        return "F"
    if texto.startswith("i"):
        return "I"
    return None


def row_para_dict(row, nomes_colunas):
    return {
        nome: normalizar_valor(valor)
        for nome, valor in zip(nomes_colunas, row)
    }


def fetchall_dict(cursor):
    nomes_colunas = [desc[0].strip().upper() for desc in cursor.description]
    return [row_para_dict(row, nomes_colunas) for row in cursor.fetchall()]


def fetchone_dict(cursor):
    nomes_colunas = [desc[0].strip().upper() for desc in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return row_para_dict(row, nomes_colunas)


def colunas_tabela(cursor, tabela):
    cursor.execute(
        """
        SELECT rf.RDB$FIELD_NAME
        FROM RDB$RELATION_FIELDS rf
        WHERE rf.RDB$RELATION_NAME = ?
        """,
        (tabela.upper(),),
    )
    return {str(row[0]).strip().upper() for row in cursor.fetchall()}


def nome_identificador_seguro(nome):
    nome = normalizar_texto(nome, 63)
    if not nome:
        return None

    nome = nome.upper()
    if not IDENT_RE.match(nome):
        raise ValueError(f"Identificador Firebird inválido: {nome}")
    return nome


def generator_existe(cursor, nome):
    cursor.execute(
        """
        SELECT 1
        FROM RDB$GENERATORS
        WHERE RDB$GENERATOR_NAME = ?
        """,
        (nome,),
    )
    return cursor.fetchone() is not None


def candidatos_generator(tabela):
    tabela = tabela.upper()
    env_value = os.getenv(f"SPDATA_{tabela}_GENERATOR") or os.getenv(
        f"SPDATA_{tabela}_ID_GENERATOR"
    )
    nomes = [env_value] if env_value else []
    nomes.extend([
        f"GEN_{tabela}_ID",
        f"GEN_{tabela}",
        f"{tabela}_ID_GEN",
        f"{tabela}_GEN",
        f"SQ_{tabela}",
        f"SEQ_{tabela}",
    ])
    return [nome_identificador_seguro(nome) for nome in nomes if normalizar_texto(nome)]


def proximo_id(cursor, tabela):
    for generator in candidatos_generator(tabela):
        if not generator_existe(cursor, generator):
            continue

        cursor.execute(f"SELECT GEN_ID({generator}, 1) FROM RDB$DATABASE")
        row = cursor.fetchone()
        return normalizar_int(row[0]) if row else None

    return None


def filtrar_colunas_existentes(valores, colunas):
    return {
        coluna: valor
        for coluna, valor in valores.items()
        if coluna in colunas and valor is not None
    }


def insert_returning(cursor, tabela, valores, returning):
    valores = dict(valores)
    colunas = list(valores.keys())
    placeholders = ", ".join("?" for _ in colunas)
    sql = (
        f"INSERT INTO {tabela} ({', '.join(colunas)}) "
        f"VALUES ({placeholders}) RETURNING {', '.join(returning)}"
    )
    cursor.execute(sql, tuple(valores[coluna] for coluna in colunas))
    return fetchone_dict(cursor)


def update_por_id(cursor, tabela, tabela_colunas, registro_id, valores):
    valores = filtrar_colunas_existentes(valores, tabela_colunas)
    if not valores:
        return

    atribuicoes = ", ".join(f"{coluna} = ?" for coluna in valores)
    cursor.execute(
        f"UPDATE {tabela} SET {atribuicoes} WHERE ID = ?",
        (*valores.values(), registro_id),
    )


def paciente_para_frontend(row):
    if not row:
        return None

    return {
        "idPacienteSpdata": normalizar_int(row.get("ID")),
        "id": normalizar_int(row.get("ID")),
        "prontuario": normalizar_texto(row.get("PRONT"), 50),
        "nome": normalizar_texto(row.get("NOME"), 255),
        "nomeSocial": normalizar_texto(row.get("APELIDO"), 255),
        "cpf": normalizar_cpf_frontend(row.get("CPF")),
        "dataNascimento": row.get("NASC"),
        "sexo": row.get("SEXO"),
        "celular": normalizar_texto(row.get("CELULAR"), 30) or "",
        "celularWhatsapp": normalizar_texto(row.get("CELULAR"), 30) or "",
        "telefone": normalizar_texto(row.get("FONE"), 30) or "",
        "telefoneFixo": normalizar_texto(row.get("FONE"), 30) or "",
        "email": normalizar_texto(row.get("EMAIL"), 255) or "",
        "endereco": normalizar_texto(row.get("ENDERECO"), 500) or "",
        "logradouro": normalizar_texto(row.get("ENDERECO"), 500) or "",
        "numero": normalizar_texto(row.get("NUMERO"), 30) or "",
        "complemento": normalizar_texto(row.get("COMPL"), 100) or "",
        "bairro": normalizar_texto(row.get("BAIRRO"), 120) or "",
        "cidade": normalizar_texto(row.get("CIDADE"), 120) or "",
        "uf": normalizar_texto(row.get("UF"), 2) or "",
        "estadoUf": normalizar_texto(row.get("UF"), 2) or "",
        "cep": normalizar_cep_frontend(row.get("CEP")),
        "nomeMae": normalizar_texto(row.get("MAE"), 255) or "",
        "nomePai": normalizar_texto(row.get("PAI"), 255) or "",
        "rg": normalizar_texto(row.get("IDENT"), 30) or "",
        "orgaoEmissor": normalizar_texto(row.get("ORGAO"), 20) or "",
        "codigoIbge": normalizar_texto(row.get("IBGE"), 20) or "",
    }


def select_paciente_sql(where):
    return f"""
        SELECT FIRST 50
            p.ID,
            p.PRONT,
            p.NOME,
            p.APELIDO,
            p.CPF,
            p.NASC,
            p.SEXO,
            p.CELULAR,
            p.FONE,
            p.EMAIL,
            p.ENDERECO,
            p.NUMERO,
            p.COMPL,
            p.BAIRRO,
            p.CIDADE,
            p.UF,
            p.CEP,
            p.MAE,
            p.PAI,
            p.IDENT,
            p.ORGAO,
            p.IBGE
        FROM RICADPAC p
        WHERE {where}
        ORDER BY p.NOME
    """


def buscar_pacientes_spdata(cpf=None, prontuario=None, paciente_id=None, search=None):
    filtros = []
    params = []

    paciente_id = normalizar_int(paciente_id)
    if paciente_id is not None:
        filtros.append("p.ID = ?")
        params.append(paciente_id)

    cpf = normalizar_cpf(cpf)
    if cpf:
        filtros.append("p.CPF = ?")
        params.append(int(cpf))

    prontuario = normalizar_texto(prontuario, 50)
    if prontuario:
        filtros.append("CAST(p.PRONT AS VARCHAR(50)) = ?")
        params.append(prontuario)

    search = normalizar_texto(search, 120)
    if search:
        filtros.append(
            "(p.NOME CONTAINING ? OR CAST(p.CPF AS VARCHAR(20)) CONTAINING ? OR CAST(p.PRONT AS VARCHAR(50)) CONTAINING ?)"
        )
        params.extend([search, search, search])

    if not filtros:
        raise ValueError("Informe cpf, prontuário, id ou busca para pesquisar paciente")

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        cursor.execute(select_paciente_sql(" AND ".join(filtros)), tuple(params))
        return [paciente_para_frontend(row) for row in fetchall_dict(cursor)]


def buscar_paciente_por_id(cursor, paciente_id):
    cursor.execute(select_paciente_sql("p.ID = ?"), (paciente_id,))
    return fetchone_dict(cursor)


def buscar_paciente_por_cpf(cursor, cpf):
    cpf = normalizar_cpf(cpf)
    if not cpf:
        return None

    cursor.execute(select_paciente_sql("p.CPF = ?"), (int(cpf),))
    return fetchone_dict(cursor)


def valores_paciente_spdata(payload):
    cpf = normalizar_cpf_firebird(payload.get("cpf"))
    data_nascimento = normalizar_data(payload.get("dataNascimento"))
    agora = datetime.now().replace(microsecond=0)
    return {
        "TIPOPAC": "I",
        "OTMU": "F",
        "NOME": normalizar_texto(payload.get("nomeCompleto") or payload.get("nome"), 70),
        "APELIDO": normalizar_texto(payload.get("nomeSocial"), 70),
        "CPF": cpf,
        "NASC": data_nascimento,
        "SEXO": normalizar_sexo(payload.get("sexoBiologico") or payload.get("sexo")),
        "MAE": None
        if payload.get("maeDesconhecida")
        else normalizar_texto(payload.get("nomeMae"), 70),
        "PAI": normalizar_texto(payload.get("nomePai"), 70),
        "IDENT": normalizar_texto(payload.get("rg"), 15),
        "ORGAO": normalizar_texto(payload.get("orgaoEmissor"), 5),
        "CELULAR": normalizar_texto(payload.get("celularWhatsapp") or payload.get("celular"), 15),
        "FONE": normalizar_texto(payload.get("telefoneFixo") or payload.get("telefone"), 15),
        "EMAIL": normalizar_texto(payload.get("email"), 50),
        "CEP": normalizar_cep_firebird(payload.get("cep")),
        "ENDERECO": normalizar_texto(payload.get("logradouro") or payload.get("endereco"), 40),
        "NUMERO": normalizar_digitos_int(payload.get("numero")),
        "COMPL": normalizar_texto(payload.get("complemento"), 15),
        "BAIRRO": normalizar_texto(payload.get("bairro"), 30),
        "CIDADE": normalizar_texto(payload.get("cidade"), 30),
        "UF": normalizar_texto(payload.get("estadoUf") or payload.get("uf"), 2),
        "IBGE": normalizar_digitos_int(payload.get("codigoIbge")),
        "NAC": normalizar_texto(payload.get("nacionalidade"), 40) or "BRASILEIRA",
        "NACIONALIDADE": 10,
        "DTCAD": agora.date(),
        "DATA_HORA_INCLUSAO": agora,
        "DATA_HORA_ULTIMA_ATUALIZACAO": agora,
        "ATIVO": "T",
        "REALIZA_CHAMADO_APELIDO_SOCIAL": "F",
    }


def salvar_paciente_spdata(payload):
    valores = valores_paciente_spdata(payload)
    nome = valores.get("NOME")
    if not nome:
        raise ValueError("Nome do paciente é obrigatório")

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        colunas = colunas_tabela(cursor, "RICADPAC")
        valores = normalizar_referencias_paciente(cursor, valores)

        paciente = None
        paciente_id = normalizar_int(payload.get("idPacienteSpdata") or payload.get("id"))
        if paciente_id is not None:
            paciente = buscar_paciente_por_id(cursor, paciente_id)

        if paciente is None and valores.get("CPF"):
            paciente = buscar_paciente_por_cpf(cursor, valores.get("CPF"))

        if paciente:
            paciente_id = normalizar_int(paciente.get("ID"))
            valores_update = dict(valores)
            for campo in (
                "DTCAD",
                "DATA_HORA_INCLUSAO",
                "TIPOPAC",
                "OTMU",
                "NACIONALIDADE",
                "REALIZA_CHAMADO_APELIDO_SOCIAL",
            ):
                valores_update.pop(campo, None)
            update_por_id(cursor, "RICADPAC", colunas, paciente_id, valores_update)
            paciente = buscar_paciente_por_id(cursor, paciente_id)
            connection.commit()
            return {"paciente": paciente_para_frontend(paciente), "created": False}

        valores_insert = filtrar_colunas_existentes(valores, colunas)
        if "ID" in colunas:
            novo_id = proximo_id(cursor, "RICADPAC")
            if novo_id is not None:
                valores_insert["ID"] = novo_id
                if "ID_RICADPAC_UNIFICADO" in colunas:
                    valores_insert["ID_RICADPAC_UNIFICADO"] = novo_id

        try:
            paciente = insert_returning(cursor, "RICADPAC", valores_insert, ["ID"])
        except Exception:
            connection.rollback()
            raise

        paciente_id = normalizar_int((paciente or {}).get("ID") or valores_insert.get("ID"))
        paciente = buscar_paciente_por_id(cursor, paciente_id) if paciente_id else None
        connection.commit()
        return {"paciente": paciente_para_frontend(paciente), "created": True}


def buscar_tbcbo_atendimento(cursor, medico_id=None, crm=None, nome=None):
    filtros = []
    params = []

    medico_id = normalizar_int(medico_id)
    if medico_id is not None:
        filtros.append("p.ID = ?")
        params.append(medico_id)

    crm = normalizar_texto(crm, 50)
    if crm:
        filtros.append("CAST(cb.COD AS VARCHAR(50)) = ?")
        params.append(crm)

    nome = normalizar_texto(nome, 120)
    if nome:
        filtros.append("p.NOME CONTAINING ?")
        params.append(nome)

    if not filtros:
        raise ValueError("Médico é obrigatório")

    sql = f"""
        SELECT FIRST 1
            cb.ID AS ID_TBCBOPRO,
            cb.COD AS CRM_MEDICO,
            p.ID AS ID_MEDICO_SPDATA,
            p.NOME AS MEDICO
        FROM TBCBOPRO cb
        INNER JOIN TBPROFIS p
            ON p.ID = cb.ID_TBPROFIS
        WHERE ({' OR '.join(filtros)})
        ORDER BY cb.ATIVO DESC, cb.ID
    """
    cursor.execute(sql, tuple(params))
    medico = fetchone_dict(cursor)
    if not medico:
        raise LookupError("Médico não encontrado no SPDATA")
    return medico


def buscar_medico_payload(cursor, payload):
    crm = normalizar_texto(
        payload.get("crmAtendimento")
        or payload.get("crm_atendimento_spdata")
        or payload.get("crm"),
        50,
    )
    nome = normalizar_texto(payload.get("nomeMedico") or payload.get("medico"), 120)
    medico_spdata_id = normalizar_int(payload.get("medicoSpdataId") or payload.get("idMedicoSpdata"))
    medico_local_id = normalizar_int(payload.get("medicoId"))

    if (not crm and not nome and medico_spdata_id is None) and medico_local_id is not None:
        medico_local = db.session.get(Medico, medico_local_id)
        if medico_local:
            crm = normalizar_texto(medico_local.crm_atendimento_spdata or medico_local.crm, 50)
            medico_spdata_id = medico_local.spdata_id

    return buscar_tbcbo_atendimento(cursor, medico_id=medico_spdata_id, crm=crm, nome=nome)


def buscar_procedimento_atendimento(cursor, payload):
    procedimento_id = normalizar_int(
        payload.get("procedimentoIdSpdata")
        or payload.get("idProcedimentoSpdata")
        or payload.get("spdataTpId")
    )
    procedimento_local_id = normalizar_int(payload.get("procedimentoId"))
    codigo = normalizar_texto(
        payload.get("codigoProcedimentoSpdata") or payload.get("codigoProcedimento"),
        50,
    )
    nome = normalizar_texto(payload.get("nomeProcedimento") or payload.get("procedimento"), 120)

    if procedimento_id is None and procedimento_local_id is not None:
        procedimento_local = db.session.get(Procedimento, procedimento_local_id)
        if procedimento_local:
            procedimento_id = procedimento_local.spdata_tp_id
            codigo = codigo or normalizar_texto(procedimento_local.codigo_procedimento, 50)

    if procedimento_id is None and not codigo and not nome:
        return None

    filtros = []
    params = []
    if procedimento_id is not None:
        filtros.append("p.ID = ?")
        params.append(procedimento_id)
    if codigo:
        filtros.append("CAST(p.COD_PROCEDIMENTO AS VARCHAR(50)) = ?")
        params.append(codigo)
    if nome:
        filtros.append("p.NOME CONTAINING ?")
        params.append(nome)

    sql = f"""
        SELECT FIRST 1
            p.ID,
            p.COD_PROCEDIMENTO,
            p.NOME
        FROM TBPROCTO p
        WHERE {' OR '.join(filtros)}
        ORDER BY p.NOME
    """
    cursor.execute(sql, tuple(params))
    return fetchone_dict(cursor)


def buscar_atendimento_existente(cursor, paciente_id, id_tbcbo, unidade, data_hora, centro_custo=None):
    inicio = data_hora.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = data_hora.replace(hour=23, minute=59, second=59, microsecond=999999)
    centro_custo = normalizar_int(centro_custo or unidade.codigo_spdata_centro_custo)
    sql = """
        SELECT FIRST 1
            a.ID AS SPDATA_ATENDIMENTO_ID,
            a.COD_ATENDIMENTO
        FROM ATCABECATEND a
        WHERE a.ID_RICADPAC = ?
          AND a.ID_TBCBOPRO_ATENDIMENTO = ?
          AND a.ID_TBCENCUS = ?
          AND a.DATA_HORA_ENTRADA BETWEEN ? AND ?
        ORDER BY a.ID
    """
    cursor.execute(
        sql,
        (
            paciente_id,
            id_tbcbo,
            centro_custo,
            inicio,
            fim,
        ),
    )
    return fetchone_dict(cursor)


def select_atendimento_sql(where):
    return f"""
        SELECT FIRST 1
            a.ID AS SPDATA_ATENDIMENTO_ID,
            a.COD_ATENDIMENTO,
            a.ID_RICADPAC AS ID_PACIENTE_SPDATA,
            a.DATA_HORA_ENTRADA,
            a.DATA_HORA_ALTA_MEDICA,
            a.OBS_ATENDIMENTO,
            a.ID_TBCONVEN AS ID_CONVENIO_SPDATA,
            convenio.NOME AS CONVENIO_NOME,
            a.ID_TBCENCUS AS ID_CENTRO_CUSTO_SPDATA,
            procedimento.COD_PROCEDIMENTO AS COD_PROCEDIMENTO_SPDATA,
            procedimento.NOME AS PROCEDIMENTO_SPDATA,
            paciente.PRONT AS PRONTUARIO,
            paciente.NOME AS PACIENTE,
            paciente.APELIDO AS PACIENTE_NOME_SOCIAL,
            paciente.NASC AS DATA_NASCIMENTO,
            paciente.SEXO AS SEXO,
            paciente.CELULAR AS CELULAR,
            paciente.EMAIL AS EMAIL,
            paciente.CPF AS CPF,
            paciente.ENDERECO AS ENDERECO,
            medico.ID AS ID_MEDICO_SPDATA,
            medico.NOME AS MEDICO,
            tb.COD AS CRM_MEDICO
        FROM ATCABECATEND a
        INNER JOIN RICADPAC paciente
            ON paciente.ID = a.ID_RICADPAC
        INNER JOIN TBCBOPRO tb
            ON a.ID_TBCBOPRO_ATENDIMENTO = tb.ID
        INNER JOIN TBPROFIS medico
            ON tb.ID_TBPROFIS = medico.ID
        LEFT JOIN TBCONVEN convenio
            ON convenio.COD = a.ID_TBCONVEN
        LEFT JOIN TBPROCTO procedimento
            ON procedimento.ID = a.ID_TBPROCTO
        WHERE {where}
    """


def buscar_atendimento_completo(cursor, spdata_atendimento_id):
    cursor.execute(
        select_atendimento_sql("a.ID = ?"),
        (spdata_atendimento_id,),
    )
    return fetchone_dict(cursor)


def observacao_atendimento(payload):
    observacoes = []
    obs = normalizar_texto(payload.get("observacao") or payload.get("obs"), 500)
    if obs:
        observacoes.append(obs)

    if payload.get("ehRetorno"):
        observacoes.append("Retorno: sim")
    if payload.get("tipoProcedimento"):
        observacoes.append(f"Tipo: {payload.get('tipoProcedimento')}")
    if payload.get("modalidade"):
        observacoes.append(f"Modalidade: {payload.get('modalidade')}")

    responsavel = payload.get("responsavel") if isinstance(payload.get("responsavel"), dict) else {}
    nome_responsavel = normalizar_texto(responsavel.get("nome"), 70)
    if nome_responsavel:
        observacoes.append(f"Responsável: {nome_responsavel}")

    return " | ".join(observacoes)[:500] or None


def criar_atendimento_firebird(cursor, tabela_colunas, payload, unidade, paciente_id, medico, procedimento, data_hora):
    agora = datetime.now().replace(microsecond=0)
    centro_custo = normalizar_int(payload.get("centroCustoNumero")) or normalizar_int(unidade.codigo_spdata_centro_custo)
    valores = {
        "ID_RICADPAC": paciente_id,
        "DATA_HORA_ENTRADA": data_hora,
        "DATA_HORA_ALTA_MEDICA": None,
        "OBS_ATENDIMENTO": observacao_atendimento(payload),
        "ID_TBCONVEN": normalizar_int(payload.get("idConvenioSpdata") or payload.get("convenioId") or payload.get("numeroConvenio")),
        "MATRICULA": normalizar_texto(payload.get("matricula"), 30),
        "DATA_VALID_CARTEIRA_CONVENIO": normalizar_data_validade(payload.get("validade")),
        "GUIA": normalizar_texto(payload.get("guiaAutorizacao") or payload.get("guia"), 20),
        "ID_TBCENCUS": centro_custo,
        "ID_TBCBOPRO_ATENDIMENTO": normalizar_int(medico.get("ID_TBCBOPRO")),
        "ID_TBPROCTO": normalizar_int((procedimento or {}).get("ID")),
        "ID_TBESPEC": normalizar_int(payload.get("idEspecialidadeSpdata")),
        "ID_TBUNIDAD": normalizar_int(payload.get("idUnidadeSpdata")),
        "TP_ATENDIMENTO": normalizar_tipo_atendimento(payload.get("tipoAtendimento")),
        "ANO_MES_PROCESSAMENTO": normalizar_int(payload.get("anoMesProcessamento")) or int(data_hora.strftime("%Y%m")),
        "DATA_HORA_INCLUSAO": agora,
        "DATA_HORA_ULTIMA_ATUALIZACAO": agora,
        "ATIVO": "T",
        "CARATER_ATEND": normalizar_int(payload.get("caraterAtendimento") or payload.get("caraterSolicitacao")),
        "ATENDIMENTO_RN_TISS": "T" if payload.get("recemNascido") else None,
        "ATENDIMENTO_RETORNO": "T" if payload.get("ehRetorno") else None,
    }

    valores_insert = filtrar_colunas_existentes(valores, tabela_colunas)
    novo_id = proximo_id(cursor, "ATCABECATEND") if "ID" in tabela_colunas else None
    if novo_id is not None:
        valores_insert["ID"] = novo_id
        if "COD_ATENDIMENTO" in tabela_colunas:
            valores_insert["COD_ATENDIMENTO"] = novo_id
    elif "COD_ATENDIMENTO" in tabela_colunas:
        cod_payload = normalizar_int(payload.get("codAtendimento") or payload.get("registro"))
        if cod_payload is not None:
            valores_insert["COD_ATENDIMENTO"] = cod_payload

    returning = ["ID"]
    if "COD_ATENDIMENTO" in tabela_colunas:
        returning.append("COD_ATENDIMENTO")

    row = insert_returning(cursor, "ATCABECATEND", valores_insert, returning)
    spdata_atendimento_id = normalizar_int((row or {}).get("ID") or valores_insert.get("ID"))
    cod_atendimento = normalizar_int((row or {}).get("COD_ATENDIMENTO"))

    if spdata_atendimento_id and not cod_atendimento and "COD_ATENDIMENTO" in tabela_colunas:
        cod_atendimento = spdata_atendimento_id
        cursor.execute(
            "UPDATE ATCABECATEND SET COD_ATENDIMENTO = ? WHERE ID = ?",
            (cod_atendimento, spdata_atendimento_id),
        )

    return spdata_atendimento_id


def sincronizar_atendimento_criado(item, unidade):
    spdata_atendimento_id = normalizar_int(item.get("SPDATA_ATENDIMENTO_ID"))
    existentes = _atendimentos_spdata_por_id([spdata_atendimento_id])
    _aplicar_atendimentos_spdata([item], existentes, unidade)
    db.session.commit()
    return db.session.execute(
        select(MedSpdataAtendimento).where(
            MedSpdataAtendimento.spdata_atendimento_id == spdata_atendimento_id
        )
    ).scalars().first()


def salvar_atendimento_spdata(payload, usuario_id, unidade_id=None):
    unidade = resolver_unidade_usuario(usuario_id, unidade_id)
    centro_custo = normalizar_int(payload.get("centroCustoNumero")) or unidade.codigo_spdata_centro_custo
    if not centro_custo:
        raise ValueError("Unidade sem código SPDATA de centro de custo configurado")

    paciente_id = normalizar_int(payload.get("idPacienteSpdata") or payload.get("pacienteId"))
    if paciente_id is None:
        raise ValueError("Paciente SPDATA é obrigatório")

    data_atendimento = normalizar_data(payload.get("data") or payload.get("dataAtendimento") or payload.get("dataEntrada"))
    hora_atendimento = normalizar_hora(payload.get("horario") or payload.get("hora") or payload.get("horaEntrada"))
    if not data_atendimento or not hora_atendimento:
        raise ValueError("Data e horário do atendimento são obrigatórios")

    data_hora = datetime.combine(data_atendimento, hora_atendimento)

    with ConnectionDBFireBird() as connection:
        cursor = connection.cursor()
        paciente = buscar_paciente_por_id(cursor, paciente_id)
        if not paciente:
            raise LookupError("Paciente não encontrado no SPDATA")

        medico = buscar_medico_payload(cursor, payload)
        procedimento = buscar_procedimento_atendimento(cursor, payload)

        existente = buscar_atendimento_existente(
            cursor,
            paciente_id,
            normalizar_int(medico.get("ID_TBCBOPRO")),
            unidade,
            data_hora,
            centro_custo=centro_custo,
        )

        if existente:
            spdata_atendimento_id = normalizar_int(existente.get("SPDATA_ATENDIMENTO_ID"))
            created = False
        else:
            colunas = colunas_tabela(cursor, "ATCABECATEND")
            try:
                spdata_atendimento_id = criar_atendimento_firebird(
                    cursor,
                    colunas,
                    payload,
                    unidade,
                    paciente_id,
                    medico,
                    procedimento,
                    data_hora,
                )
            except Exception:
                connection.rollback()
                raise
            connection.commit()
            created = True

        item = buscar_atendimento_completo(cursor, spdata_atendimento_id)

    if not item:
        raise LookupError("Atendimento criado, mas não encontrado no SPDATA")

    spdata = sincronizar_atendimento_criado(item, unidade)
    convenios_por_codigo = buscar_convenios_locais([spdata.id_convenio_spdata])
    return {
        "created": created,
        "atendimento": agenda_para_frontend(spdata, None, convenios_por_codigo),
    }


def salvar_novo_atendimento_spdata(payload, usuario_id, unidade_id=None):
    paciente_payload = payload.get("paciente") if isinstance(payload.get("paciente"), dict) else payload
    atendimento_payload = payload.get("atendimento") if isinstance(payload.get("atendimento"), dict) else payload
    responsavel_payload = payload.get("responsavel") if isinstance(payload.get("responsavel"), dict) else {}

    paciente_resultado = salvar_paciente_spdata(paciente_payload)
    paciente = paciente_resultado.get("paciente") or {}
    atendimento_completo = {
        **atendimento_payload,
        "responsavel": responsavel_payload,
        "idPacienteSpdata": paciente.get("idPacienteSpdata"),
    }

    atendimento_resultado = salvar_atendimento_spdata(atendimento_completo, usuario_id, unidade_id)
    return {
        "paciente": paciente,
        "pacienteCreated": paciente_resultado.get("created", False),
        "atendimento": atendimento_resultado.get("atendimento"),
        "atendimentoCreated": atendimento_resultado.get("created", False),
    }


def listar_convenios_recepcao(search=None):
    query = select(MedSpdataConvenio).order_by(MedSpdataConvenio.nome)
    termo = normalizar_texto(search, 120)
    if termo:
        like = f"%{termo}%"
        query = query.where(
            or_(
                MedSpdataConvenio.nome.ilike(like),
                cast(MedSpdataConvenio.codigo_spdata, String).ilike(like),
            )
        )

    return [
        {
            "idConvenioSpdata": convenio.codigo_spdata,
            "codigoSpdata": convenio.codigo_spdata,
            "nome": convenio.nome,
            "registroAns": convenio.registro_ans,
        }
        for convenio in db.session.execute(query.limit(50)).scalars().all()
    ]


def listar_procedimentos_recepcao(search=None):
    termo = normalizar_texto(search, 120)
    query = select(Procedimento).order_by(Procedimento.nome)
    if termo:
        like = f"%{termo}%"
        query = query.where(
            or_(
                Procedimento.nome.ilike(like),
                cast(Procedimento.codigo_procedimento, String).ilike(like),
                cast(Procedimento.proc_ref_tuss, String).ilike(like),
            )
        )

    return [
        {
            "id": procedimento.id,
            "spdataTpId": procedimento.spdata_tp_id,
            "nome": procedimento.nome,
            "codigoProcedimento": procedimento.codigo_procedimento,
            "codigoTuss": procedimento.proc_ref_tuss,
        }
        for procedimento in db.session.execute(query.limit(50)).scalars().all()
    ]


def medico_para_dict(usuario, medico):
    return {
        "id": medico.id,
        "usuarioId": usuario.id,
        "nome": usuario.nome_completo,
        "spdataId": medico.spdata_id,
        "crm": medico.crm,
        "crmAtendimento": medico.crm_atendimento_spdata,
        "especialidade": medico.especialidade,
    }


def listar_medicos_recepcao(unidade_id=None):
    query = (
        select(Usuario, Medico)
        .join(Medico, Medico.usuario_id == Usuario.id)
        .where(
            Usuario.role == "medico",
            Usuario.ativo.is_(True),
            Medico.ativo.is_(True),
        )
        .order_by(Usuario.nome_completo)
    )

    if unidade_id:
        query = query.join(
            UsuarioUnidade,
            UsuarioUnidade.usuario_id == Usuario.id,
        ).where(
            UsuarioUnidade.unidade_id == unidade_id,
            UsuarioUnidade.ativo.is_(True),
        )

    return [
        medico_para_dict(usuario, medico)
        for usuario, medico in db.session.execute(query).all()
    ]
