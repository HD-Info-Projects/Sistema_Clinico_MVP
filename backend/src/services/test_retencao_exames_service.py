from datetime import date, datetime
from types import SimpleNamespace

from src.services.retencao_exames_service import (
    encontrar_realizacao,
    indexar_realizacoes,
    parametros_busca_spdata,
    solicitacao_para_item,
)


def test_retencao_casa_realizacao_por_nome_quando_solicitacao_nao_tem_exame_id():
    nome_exame = "U.S. APARELHO URINARIO (RINS E BEXIGA)"
    solicitacao = SimpleNamespace(
        id=6,
        tipo_exame=nome_exame,
        created_at=datetime(2026, 7, 8, 14, 2, 21),
    )
    atendimento = SimpleNamespace(
        spdata_atendimento_id=327773,
        spdata_paciente_id=83982,
        paciente_nome="JULIANA FERNANDES DE MELO",
        paciente_cpf="95931970363",
    )
    spdata = SimpleNamespace(
        id_paciente_spdata=83982,
        cpf="95931970363",
        prontuario="84058",
        paciente="JULIANA FERNANDES DE MELO",
        medico="Medico nao informado",
        crm_medico="",
        id_convenio_spdata=1,
        celular="",
        telefone="",
    )
    convenio = SimpleNamespace(nome="Convenio")
    medico = SimpleNamespace(especialidade="Radiologia")
    realizacao_spdata = {
        "ID_EXAME_LANCAMENTO": 757560,
        "ID_SICADATE": 212743,
        "ID_PACIENTE_SPDATA": 83982,
        "PRONT": "84058",
        "CPF": "95931970363",
        "EXAME": "APUR",
        "ATO": 24,
        "EXAME_NOME": nome_exame,
        "DATA_EXAME": date(2026, 7, 20),
        "CODAMB_CONVENIO": "40901157",
        "VALOR_ESTIMADO": 260,
    }

    params = parametros_busca_spdata([(solicitacao, atendimento, None, spdata, convenio, medico)])
    indice = indexar_realizacoes([realizacao_spdata])
    realizacao = encontrar_realizacao(solicitacao, atendimento, None, spdata, indice)
    item = solicitacao_para_item(
        solicitacao,
        atendimento,
        None,
        spdata,
        convenio,
        medico,
        realizacao,
        hoje=date(2026, 7, 20),
    )

    assert params["codigos"] == []
    assert params["nomes_sem_codigo"] == [nome_exame]
    assert realizacao == realizacao_spdata
    assert item["status"] == "realizado"
    assert item["codigoExame"] == "APUR"
    assert item["tipoExame"] == "ultrassonografia"
    assert item["tipoExameCodigo"] == "24"
    assert item["tipoExameLabel"] == "Ultrassonografia"
    assert item["especialidade"] == "Radiologia"
    assert item["dataRealizacao"] == "2026-07-20"
    assert item["pendencia"] == ""


def test_retencao_classifica_tipo_exame_pelo_ato_local():
    solicitacao = SimpleNamespace(
        id=7,
        tipo_exame="HEMOGRAMA COMPLETO",
        created_at=datetime(2026, 8, 24, 20, 16, 43),
    )
    atendimento = SimpleNamespace(
        spdata_atendimento_id=346046,
        spdata_paciente_id=1,
        paciente_nome="Paciente",
        paciente_cpf="12345678900",
        unidade_id=1,
    )
    exame = SimpleNamespace(
        codigo_alfanumerico="HG",
        ato="15",
        codigo_amb="28040481",
        nome="HEMOGRAMA COMPLETO",
    )
    spdata = SimpleNamespace(
        id_paciente_spdata=1,
        cpf="12345678900",
        prontuario="123",
        paciente="Paciente",
        medico="Médico",
        crm_medico="1234",
        id_convenio_spdata=3,
        celular="",
        telefone="",
        unidade_id=1,
    )
    convenio = SimpleNamespace(nome="Cortesia")
    medico = SimpleNamespace(especialidade="Cardiologia")

    item = solicitacao_para_item(
        solicitacao,
        atendimento,
        exame,
        spdata,
        convenio,
        medico,
        None,
        hoje=date(2026, 8, 25),
    )

    assert item["tipoExame"] == "patologia-clinica"
    assert item["tipoExameCodigo"] == "15"
    assert item["tipoExameLabel"] == "Patologia Clínica"
    assert item["especialidade"] == "Cardiologia"


def test_retencao_classifica_tipo_exame_por_nome_antes_do_ato():
    solicitacao = SimpleNamespace(
        id=8,
        tipo_exame="RESSONÂNCIA DO CRÂNIO",
        created_at=datetime(2026, 8, 24, 20, 16, 43),
    )
    atendimento = SimpleNamespace(
        spdata_atendimento_id=346046,
        spdata_paciente_id=1,
        paciente_nome="Paciente",
        paciente_cpf="12345678900",
        unidade_id=1,
    )
    exame = SimpleNamespace(
        codigo_alfanumerico="RMC",
        ato="16",
        codigo_amb="0",
        nome="RESSONÂNCIA DO CRÂNIO",
    )
    spdata = SimpleNamespace(
        id_paciente_spdata=1,
        cpf="12345678900",
        prontuario="123",
        paciente="Paciente",
        medico="Médico",
        crm_medico="1234",
        id_convenio_spdata=3,
        celular="",
        telefone="",
        unidade_id=1,
    )

    item = solicitacao_para_item(
        solicitacao,
        atendimento,
        exame,
        spdata,
        SimpleNamespace(nome="Cortesia"),
        None,
        None,
        hoje=date(2026, 8, 25),
    )

    assert item["tipoExame"] == "ressonancia-magnetica"
    assert item["tipoExameCodigo"] == "26"
    assert item["tipoExameLabel"] == "Ressonância Magnética"
    assert item["especialidade"] == "Especialidade não informada"
