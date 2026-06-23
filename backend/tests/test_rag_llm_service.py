from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.services import rag_llm_service


def _settings(**overrides):
    base = {
        "rag_llm_provider": "deepseek",
        "rag_llm_api_key": None,
        "rag_llm_model": None,
        "rag_embedding_provider": "gemini",
        "rag_embedding_api_key": "gemini-key",
        "rag_max_context_tokens": 6000,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_resolve_llm_settings_uses_embedding_provider_key_when_llm_key_missing(monkeypatch):
    monkeypatch.setattr(rag_llm_service, "get_settings", lambda: _settings())

    provider, api_key, model = rag_llm_service._resolve_llm_settings()

    assert provider == "gemini"
    assert api_key == "gemini-key"
    assert model == "gemini-2.0-flash"


def test_gemini_stream_tries_fallback_model_after_configured_model_failure(monkeypatch):
    calls: list[str] = []

    def fake_stream(api_key: str, model: str, prompt: str) -> list[str]:
        calls.append(model)
        if model == "bad-model":
            raise RuntimeError("model unavailable")
        return ["grounded answer"]

    monkeypatch.setattr(rag_llm_service, "_stream_gemini_sync", fake_stream)
    monkeypatch.setitem(rag_llm_service.PROVIDER_CONFIGS["gemini"], "fallback_models", ("gemini-2.0-flash",))

    async def collect() -> str:
        chunks = []
        async for token in rag_llm_service._stream_gemini(
            "key",
            "bad-model",
            ["[event:E1] Silk Board waterlogging context"],
            [],
            "What is happening?",
            "citizen",
        ):
            chunks.append(token)
        return "".join(chunks)

    assert asyncio.run(collect()) == "grounded answer"
    assert calls == ["bad-model", "gemini-2.0-flash"]
