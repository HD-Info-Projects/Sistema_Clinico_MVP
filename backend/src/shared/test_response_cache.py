from src.shared import response_cache


class RedisIndisponivelFake:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def set_if_absent(self, *_args, **_kwargs):
        return None


def test_marcar_se_ausente_nao_suprime_evento_quando_redis_indisponivel(monkeypatch):
    monkeypatch.setattr(response_cache, "ConnectionDBRedis", RedisIndisponivelFake)

    assert response_cache.marcar_se_ausente("auditoria:test", 60, usuario_id=1) is True
