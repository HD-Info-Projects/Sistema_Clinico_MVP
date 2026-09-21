"""Testes de arquitetura do monólito modular (somente leitura, usando ast).

Regras verificadas:
- Todos os pacotes de ``src.modules`` (e suas fachadas models/service/routes)
  devem importar sem erro.
- ``src.modules.*`` não pode criar novas dependências para a camada legada
  (``src.routes.*``, ``src.services.*``, ``src.models.db.*``). O allowlist
  documenta a dívida atual e deve encolher conforme as próximas fases.
- Nenhum módulo pode importar símbolos privados (``_*``) de outro módulo,
  exceto os casos listados no allowlist.

Estes testes dependem apenas da biblioteca padrão para as regras de direção,
portanto rodam mesmo sem as dependências de terceiros instaladas. O teste de
importação exige o ambiente com dependências (flask, sqlalchemy, etc).
"""

import ast
import importlib
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parent
MODULES_DIR = BACKEND_SRC / "modules"

MODULOS_LEGADO_PROIBIDOS = (
    "src.routes.",
    "src.services.",
    "src.models.db.",
)

# Dívida atual: imports de código legado oriundos de src/modules.
# Chave: caminho relativo à pasta src/modules. Valor: raiz do módulo importado.
LEGADO_ALLOWLIST = {
    "agenda/check_in.py": {
        "src.services.auditoria_service",
        "src.models.db.handler_fb_db",
    },
    "agenda/routes.py": {
        "src.services.auditoria_service",
        "src.services.no_show_service",
        "src.services.spdata_atendimentos_service",
    },
    "agenda/service.py": {
        "src.services.no_show_service",
        "src.services.spdata_atendimentos_service",
    },
    "atendimentos/routes.py": {"src.services.auditoria_service"},
    "atendimentos/service.py": {"src.services.spdata_atendimentos_service"},
    "auth/routes.py": {
        "src.services.auditoria_service",
        "src.services.medicos_spdata_service",
    },
    "chamadas/service.py": {"src.services.auditoria_service"},
    "clinico/prontuario.py": {
        "src.services.auditoria_service",
        "src.services.spdata_atendimentos_service",
        "src.models.db.handler_fb_db",
        "src.models.db.handler_redis_db",
    },
    "clinico/routes.py": {
        "src.routes.modelo_documento_medico_route",
        "src.routes.modelo_orientacao_exame_route",
        "src.routes.modelo_solicitacao_anamnese_route",
        "src.routes.modelo_solicitacao_exames_route",
        "src.routes.modelo_solicitacao_medicos_route",
    },
    "clinico/service.py": {
        "src.services.padroes_medico_service",
        "src.services.spdata_atendimentos_service",
    },
    "documentos/routes.py": {"src.services.auditoria_service"},
    "documentos/service.py": {"src.services.documentos_medicos_service"},
    "lgpd/service.py": {
        "src.services.auditoria_service",
        "src.services.retencao_exames_service",
    },
    "pacs/routes.py": {"src.services.auditoria_service"},
    "pacientes/service.py": {
        "src.services.spdata_agenda_service",
        "src.services.spdata_atendimentos_service",
        "src.services.spdata_recepcao_service",
    },
    "recepcao/routes.py": {"src.services.auditoria_service"},
    "recepcao/service.py": {"src.services.spdata_recepcao_service"},
    "usuarios/routes.py": {"src.services.medicos_spdata_service"},
}

# Dívida atual: símbolos privados importados entre módulos distintos.
# Tupla: (caminho relativo a src/modules, módulo importado, nome privado).
PRIVADOS_ALLOWLIST = {
    (
        "pacs/routes.py",
        "src.modules.clinico.prontuario",
        "_referencia_autorizada_paciente",
    ),
}

# Arquivos que atuam como raiz de composição do namespace de módulos.
ARQUIVOS_RAIZ = {"__init__.py", "registry.py"}


def _imports_absolutos(caminho: Path):
    """Extrai (modulo, nomes, linha) de imports absolutos de um arquivo py."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    imports = []
    for node in ast.walk(arvore):
        if isinstance(node, ast.ImportFrom):
            if node.level:  # ignora imports relativos (e.g. ".models")
                continue
            modulo = node.module or ""
            nomes = tuple(a.name for a in node.names)
            imports.append((modulo, nomes, node.lineno))
        elif isinstance(node, ast.Import):
            for a in node.names:
                imports.append((a.name, tuple(), node.lineno))
    return imports


def _arquivos_modulos() -> list[tuple[Path, str, str]]:
    """Retorna (caminho, caminho_relativo, nome_do_pacote) para cada módulo py."""
    arquivos = []
    for caminho in MODULES_DIR.rglob("*.py"):
        if "__pycache__" in caminho.parts:
            continue
        relativo = caminho.relative_to(MODULES_DIR).as_posix()
        pacote = "src.modules"  # arquivos na raiz de modules (init, registry)
        if caminho.parent != MODULES_DIR:
            pacote = f"src.modules.{caminho.parent.name}"
        arquivos.append((caminho, relativo, pacote))
    return arquivos


def _lista_pacotes_modules() -> list[str]:
    return sorted(
        p.name
        for p in MODULES_DIR.iterdir()
        if p.is_dir()
        and (p / "__init__.py").exists()
        and p.name != "__pycache__"
    )


def _verificar_direcao():
    """Roda as regras AST e devolve a lista de violações encontradas."""
    violacoes = []
    for caminho, relativo, pacote in _arquivos_modulos():
        diretorio = Path(relativo).parent.as_posix()
        nome_arquivo = Path(relativo).name
        if diretorio == "." and nome_arquivo in ARQUIVOS_RAIZ:
            continue  # raiz de composição: livre para orquestrar módulos

        for modulo, nomes, linha in _imports_absolutos(caminho):
            importa_pacote_proprio = modulo == pacote or modulo.startswith(pacote + ".")

            if not importa_pacote_proprio and modulo.startswith(MODULOS_LEGADO_PROIBIDOS):
                permitido = modulo in LEGADO_ALLOWLIST.get(relativo, set())
                if not permitido:
                    violacoes.append(
                        f"{relativo}:{linha}: import do legado '{modulo}' "
                        "fora do allowlist"
                    )

            if module_startswith_modules(modulo) and not importa_pacote_proprio:
                for nome in nomes:
                    if nome.startswith("_"):
                        permitido = (
                            relativo,
                            modulo,
                            nome,
                        ) in PRIVADOS_ALLOWLIST
                        if not permitido:
                            violacoes.append(
                                f"{relativo}:{linha}: símbolo privado "
                                f"'{nome}' de {modulo} fora do allowlist"
                            )
    return violacoes


def module_startswith_modules(modulo: str) -> bool:
    return modulo == "src.modules" or modulo.startswith("src.modules.")


def test_todos_pacotes_e_fachadas_de_modulos_importam():
    falhas = []
    for nome in _lista_pacotes_modules():
        for sufixo in ("", ".models", ".service", ".routes"):
            if sufixo and not (MODULES_DIR / nome / f"{sufixo}.py").exists():
                continue  # módulo não tem essa fachada (ex.: pacs sem service.py)
            modulo = f"src.modules.{nome}{sufixo}"
            try:
                importlib.import_module(modulo)
            except Exception as exc:  # noqa: BLE001 - queremos coletar todas
                falhas.append(f"{modulo}: {type(exc).__name__}: {exc}")
    assert not falhas, "Falhas de importação em módulos:\n" + "\n".join(falhas)


def test_modules_nao_importam_camada_legada_fora_do_allowlist():
    assert not _verificar_direcao(), (
        "Novas dependências de src/modules para o legado "
        "(src.routes/src.services/src.models.db) ou símbolos privados "
        "entre módulos. Revise o allowlist ou aponte o legado para o módulo."
    )
