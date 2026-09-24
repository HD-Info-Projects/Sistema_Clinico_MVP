import time
from contextlib import contextmanager

from flask import current_app


class PerformanceProbe:
    def __init__(self, rota, **contexto):
        self.rota = rota
        self.contexto = contexto
        self.started_at = time.perf_counter()
        self.etapas = {}

    @contextmanager
    def etapa(self, nome):
        started_at = time.perf_counter()
        try:
            yield
        finally:
            self.etapas[f"{nome}_ms"] = round((time.perf_counter() - started_at) * 1000, 2)

    def marcar(self, nome, started_at):
        self.etapas[f"{nome}_ms"] = round((time.perf_counter() - started_at) * 1000, 2)

    def valor(self, nome, valor):
        self.etapas[nome] = valor

    def finalizar(self, **extras):
        total_ms = round((time.perf_counter() - self.started_at) * 1000, 2)
        payload = {
            "route": self.rota,
            **self.contexto,
            **self.etapas,
            **extras,
            "total_ms": total_ms,
        }
        current_app.logger.info(
            "performance route=%s metrics=%s",
            self.rota,
            payload,
        )
        return payload


def iniciar_probe(rota, **contexto):
    return PerformanceProbe(rota, **contexto)
