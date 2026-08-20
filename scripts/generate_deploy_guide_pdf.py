#!/usr/bin/env python3
"""Generate the current Docker VPS deployment guide PDF."""

from pathlib import Path

from generate_retention_policy_pdf import generate_document


ROOT = Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    generate_document(
        ROOT / "docs" / "DEPLOY_DOCKER_VPS.md",
        ROOT / "docs" / "DEPLOY_DOCKER_VPS.pdf",
        title="Guia de Deploy Docker na VPS",
        cover_title="Guia de Deploy\nDocker na VPS",
        subtitle="Instalação, segurança, backup e operação",
        status="Guia operacional",
        warning=(
            "Use credenciais próprias do ambiente e mantenha a chave privada age fora "
            "da VPS. Teste backup e restauração em ambiente isolado antes da produção."
        ),
    )
