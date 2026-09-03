from datetime import date, datetime, time
from types import SimpleNamespace

import pytest

from src.services import spdata_recepcao_service as service


def test_valores_paciente_spdata_normaliza_campos_reais_ricadpac():
    valores = service.valores_paciente_spdata({
        "nomeCompleto": " Maria Silva " * 10,
        "nomeSocial": " Mari " * 20,
        "cpf": "123.456.789-00",
        "dataNascimento": "1990-05-10",
        "sexoBiologico": "feminino",
        "nomeMae": " Ana Silva " * 10,
        "rg": "MG12345",
        "celularWhatsapp": "(11) 99999-8888",
        "cep": "33031-060",
        "numero": "123A",
        "estadoUf": "SP",
        "codigoIbge": "3550308",
    })

    assert valores["TIPOPAC"] == "I"
    assert valores["OTMU"] == "F"
    assert len(valores["NOME"]) == 70
    assert len(valores["APELIDO"]) == 70
    assert valores["CPF"] == 12345678900
    assert valores["NASC"] == date(1990, 5, 10)
    assert valores["SEXO"] == "F"
    assert len(valores["MAE"]) == 70
    assert valores["IDENT"] == "MG12345"
    assert valores["CEP"] == 33031060
    assert valores["NUMERO"] == 123
    assert valores["IBGE"] == 3550308
    assert valores["NAC"] == "BRASILEIRA"
    assert valores["NACIONALIDADE"] == 10
    assert valores["REALIZA_CHAMADO_APELIDO_SOCIAL"] == "F"


def test_paciente_para_frontend_normaliza_cep_e_cpf_numericos():
    paciente = service.paciente_para_frontend({
        "ID": 1,
        "NOME": "Paciente",
        "CPF": 8277593635.0,
        "CEP": 33031060,
    })

    assert paciente["cpf"] == "08277593635"
    assert paciente["cep"] == "33031060"


def test_resolver_cep_spdata_mantem_cep_existente():
    class Cursor:
        def execute(self, sql, params):
            self.sql = sql
            self.params = params

        def fetchone(self):
            if self.params == (33030000,):
                return (33030000,)
            return None

    assert service.resolver_cep_spdata(Cursor(), "33030-000") == 33030000


def test_resolver_cep_spdata_remove_cep_inexistente():
    class Cursor:
        def execute(self, sql, params):
            self.sql = sql
            self.params = params

        def fetchone(self):
            return None

    assert service.resolver_cep_spdata(Cursor(), "33031-060") is None


def test_resolver_ibge_spdata_mapeia_codigo_ibge_com_digito():
    class Cursor:
        def execute(self, sql, params):
            self.params = params

        def fetchone(self):
            if self.params == (3157807,):
                return None
            if self.params == (315780, 7):
                return (315780,)
            return None

    assert service.resolver_ibge_spdata(Cursor(), "3157807") == 315780


def test_normalizar_referencias_paciente_remove_ibge_e_cep_inexistentes():
    class Cursor:
        def execute(self, sql, params):
            self.params = params

        def fetchone(self):
            return None

    valores = service.normalizar_referencias_paciente(Cursor(), {"IBGE": 9999999, "CEP": 33031060})

    assert valores["IBGE"] is None
    assert valores["CEP"] is None


def test_select_paciente_sql_nao_usa_cnpj_cpf_inexistente():
    sql = service.select_paciente_sql("p.CPF = ?")

    assert "p.CPF" in sql
    assert "CNPJ_CPF" not in sql


def test_buscar_atendimento_existente_usa_janela_do_mesmo_dia():
    class Cursor:
        description = [("SPDATA_ATENDIMENTO_ID",), ("COD_ATENDIMENTO",)]

        def execute(self, sql, params):
            self.sql = sql
            self.params = params

        def fetchone(self):
            return (123, "123")

    cursor = Cursor()
    unidade = SimpleNamespace(codigo_spdata_centro_custo=340)
    resultado = service.buscar_atendimento_existente(
        cursor,
        paciente_id=10,
        id_tbcbo=20,
        unidade=unidade,
        data_hora=datetime(2026, 9, 2, 8, 30, 45),
    )

    assert "DATA_HORA_ENTRADA BETWEEN" in cursor.sql
    assert cursor.params[0:3] == (10, 20, 340)
    assert cursor.params[3] == datetime(2026, 9, 2, 0, 0)
    assert cursor.params[4] == datetime(2026, 9, 2, 23, 59, 59, 999999)
    assert resultado["SPDATA_ATENDIMENTO_ID"] == 123


def test_criar_atendimento_firebird_usa_externo_e_cod_numerico(monkeypatch):
    class Cursor:
        description = [("ID",), ("COD_ATENDIMENTO",)]

        def execute(self, sql, params):
            self.sql = sql
            self.params = params

        def fetchone(self):
            return (999, 999)

    cursor = Cursor()
    monkeypatch.setattr(service, "proximo_id", lambda cursor, tabela: 999)

    resultado = service.criar_atendimento_firebird(
        cursor,
        {
            "ID",
            "ID_RICADPAC",
            "COD_ATENDIMENTO",
            "TP_ATENDIMENTO",
            "ANO_MES_PROCESSAMENTO",
            "DATA_HORA_ENTRADA",
            "ID_TBCONVEN",
            "ID_TBCENCUS",
            "ID_TBCBOPRO_ATENDIMENTO",
            "ID_TBPROCTO",
            "DATA_HORA_INCLUSAO",
            "DATA_HORA_ULTIMA_ATUALIZACAO",
            "ATIVO",
            "CARATER_ATEND",
        },
        {
            "registro": "222",
            "numeroConvenio": "10",
            "tipoAtendimento": "x",
            "caraterAtendimento": "1",
        },
        SimpleNamespace(codigo_spdata_centro_custo="340"),
        paciente_id=123,
        medico={"ID_TBCBOPRO": "20"},
        procedimento={"ID": "30"},
        data_hora=datetime(2026, 9, 2, 8, 30),
    )

    assert resultado == 999
    assert "COD_ATENDIMENTO" in cursor.sql
    valores = dict(zip(
        [parte.strip() for parte in cursor.sql.split("(", 1)[1].split(")", 1)[0].split(",")],
        cursor.params,
    ))
    assert valores["COD_ATENDIMENTO"] == 999
    assert valores["TP_ATENDIMENTO"] == "E"
    assert valores["ANO_MES_PROCESSAMENTO"] == 202609
    assert valores["ID_TBCONVEN"] == 10
    assert valores["ID_TBCENCUS"] == 340
    assert valores["CARATER_ATEND"] == 1


def test_salvar_atendimento_nao_insere_quando_ja_existe(monkeypatch):
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return None

        def cursor(self):
            return SimpleNamespace()

        def commit(self):
            raise AssertionError("não deve commitar escrita Firebird para atendimento existente")

    unidade = SimpleNamespace(id=1, codigo_spdata_centro_custo=340)
    spdata = SimpleNamespace(id_convenio_spdata=10)

    monkeypatch.setattr(service, "ConnectionDBFireBird", lambda: FakeConnection())
    monkeypatch.setattr(service, "resolver_unidade_usuario", lambda usuario_id, unidade_id=None: unidade)
    monkeypatch.setattr(service, "buscar_paciente_por_id", lambda cursor, paciente_id: {"ID": paciente_id})
    monkeypatch.setattr(service, "buscar_medico_payload", lambda cursor, payload: {"ID_TBCBOPRO": 20})
    monkeypatch.setattr(service, "buscar_procedimento_atendimento", lambda cursor, payload: {"ID": 30})
    monkeypatch.setattr(
        service,
        "buscar_atendimento_existente",
        lambda cursor, paciente_id, id_tbcbo, unidade, data_hora, centro_custo=None: {
            "SPDATA_ATENDIMENTO_ID": 555,
            "COD_ATENDIMENTO": "555",
        },
    )
    monkeypatch.setattr(service, "buscar_atendimento_completo", lambda cursor, atendimento_id: {
        "SPDATA_ATENDIMENTO_ID": atendimento_id,
        "DATA_HORA_ENTRADA": datetime.combine(date(2026, 9, 2), time(8, 0)),
        "PACIENTE": "Paciente",
    })
    monkeypatch.setattr(service, "sincronizar_atendimento_criado", lambda item, unidade: spdata)
    monkeypatch.setattr(service, "buscar_convenios_locais", lambda codigos: {})
    monkeypatch.setattr(service, "agenda_para_frontend", lambda spdata, atendimento, convenios: {"id": 1})
    monkeypatch.setattr(
        service,
        "criar_atendimento_firebird",
        lambda *args, **kwargs: pytest.fail("não deve inserir atendimento duplicado"),
    )

    resultado = service.salvar_atendimento_spdata(
        {
            "idPacienteSpdata": 10,
            "crm": "123",
            "dataEntrada": "2026-09-02",
            "horaEntrada": "08:00",
        },
        usuario_id=7,
        unidade_id=1,
    )

    assert resultado == {"created": False, "atendimento": {"id": 1}}
