from __future__ import annotations

import asyncio
import hashlib
import math
import re
from functools import lru_cache

import httpx

from app.core.config import get_settings
from app.orm.rag_chunk import VECTOR_DIMENSIONS

try:  # pragma: no cover - optional provider dependency
    from google import genai
except ModuleNotFoundError:  # pragma: no cover - local fallback path
    genai = None

TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


@lru_cache(maxsize=2048)
def _fallback_embedding_cached(text: str) -> tuple[float, ...]:
    tokens = TOKEN_PATTERN.findall(text.lower()) or [text.lower() or "empty"]
    vector = [0.0] * VECTOR_DIMENSIONS
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for index, byte in enumerate(digest):
            slot = (byte + (index * 31)) % VECTOR_DIMENSIONS
            sign = 1.0 if byte % 2 == 0 else -1.0
            vector[slot] += sign * (1.0 + (byte / 255.0))
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return tuple(round(value / norm, 6) for value in vector)


def _normalize_dimensions(values: list[float]) -> list[float]:
    if len(values) == VECTOR_DIMENSIONS:
        return [float(value) for value in values]
    if len(values) > VECTOR_DIMENSIONS:
        return [float(value) for value in values[:VECTOR_DIMENSIONS]]
    padded = [float(value) for value in values]
    padded.extend([0.0] * (VECTOR_DIMENSIONS - len(values)))
    return padded


def _embed_with_gemini(api_key: str, model: str, text: str) -> list[float]:
    if genai is None:
        raise RuntimeError("google-genai dependency is not installed")
    client = genai.Client(api_key=api_key)
    
    clean_model = model.replace("models/", "") if model.startswith("models/") else model
    response = client.models.embed_content(
        model=clean_model,
        contents=text,
    )
    if not response.embeddings or not response.embeddings[0].values:
        raise RuntimeError("Gemini embedding response was empty")
    return _normalize_dimensions(list(response.embeddings[0].values))


def _embed_with_openai(api_key: str, model: str, text: str) -> list[float]:
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "input": text},
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    embedding = payload.get("data", [{}])[0].get("embedding")
    if not embedding:
        raise RuntimeError("OpenAI embedding response was empty")
    return _normalize_dimensions(list(embedding))


def _embed_with_ollama(model: str, text: str) -> list[float]:
    response = httpx.post(
        "http://127.0.0.1:11434/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    embedding = payload.get("embedding") or payload.get("data")
    if not embedding:
        raise RuntimeError("Ollama embedding response was empty")
    return _normalize_dimensions(list(embedding))


def _embed_text_sync(provider: str, api_key: str | None, model: str | None, text: str) -> tuple[float, ...]:
    provider_key = (provider or "gemini").strip().lower()
    normalized_text = (text or "").strip()
    if not normalized_text:
        return _fallback_embedding_cached("empty")

    try:
        if provider_key == "gemini" and api_key:
            return tuple(_embed_with_gemini(api_key, model or "text-embedding-004", normalized_text))
        if provider_key == "openai" and api_key:
            return tuple(_embed_with_openai(api_key, model or "text-embedding-3-small", normalized_text))
        if provider_key == "ollama":
            return tuple(_embed_with_ollama(model or "nomic-embed-text", normalized_text))
    except Exception:
        pass

    return _fallback_embedding_cached(normalized_text)


def embed_text_sync(text: str) -> list[float]:
    settings = get_settings()
    api_key = settings.rag_embedding_api_key or settings.rag_llm_api_key
    model = settings.rag_embedding_model
    return list(
        _embed_text_sync(
            settings.rag_embedding_provider,
            api_key,
            model,
            text,
        )
    )


async def embed_text(text: str) -> list[float]:
    return await asyncio.to_thread(embed_text_sync, text)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return await asyncio.gather(*(embed_text(text) for text in texts))

