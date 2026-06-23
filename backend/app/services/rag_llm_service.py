from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.roles import canonical_role

try:  # pragma: no cover - optional provider dependency
    import google.generativeai as genai
except ModuleNotFoundError:  # pragma: no cover - optional provider dependency
    genai = None

try:  # pragma: no cover - optional provider dependency
    import anthropic
except ModuleNotFoundError:  # pragma: no cover - optional provider dependency
    anthropic = None

logger = logging.getLogger(__name__)

PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
    },
    "gemini": {
        "base_url": None,
        "default_model": "gemini-2.0-flash",
        "fallback_models": ("gemini-1.5-flash",),
    },
    "anthropic": {
        "base_url": None,
        "default_model": "claude-3-5-haiku-20241022",
    },
}

MAX_HISTORY_MESSAGES = 12
FALLBACK_CHUNK_LIMIT = 4
TOKEN_SPLIT_PATTERN = re.compile(r"\S+\s*")
SOURCE_PATTERN = re.compile(r"^\[(?P<chunk_type>[^:\]]+):(?P<source_id>[^\]]+)\]\s*(?P<body>.*)$")

PUBLIC_SYSTEM_PROMPT = """
You are Sanchar Sarthi's public traffic assistant.
Answer only from the supplied retrieved context.
Never invent live telemetry, police deployment, audit history, or admin-only system details.
If the retrieved context is insufficient, say so clearly.
Keep answers calm, practical, and easy for the public to follow.
""".strip()

CONTROL_ROOM_SYSTEM_PROMPT = """
You are Sanchar Sarthi's control-room intelligence assistant.
Use only the supplied retrieved context.
You may summarize event DNA, recommendations, hotspots, citizen reports, and live updates.
Do not invent sensor feeds, enforcement actions, or external integrations that are not present in context.
If evidence is weak or incomplete, say so explicitly.
""".strip()

ADMIN_SYSTEM_PROMPT = """
You are Sanchar Sarthi's internal admin assistant.
Use only the supplied retrieved context.
You may summarize public, control-room, and admin context including audit, model-run, and map-usage records.
Do not fabricate operational outcomes or hidden system states.
Call out uncertainty whenever the indexed evidence is partial.
""".strip()


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _truncate_text_to_tokens(text: str, token_budget: int) -> str:
    char_budget = max(80, token_budget * 4)
    collapsed = " ".join((text or "").split())
    if len(collapsed) <= char_budget:
        return collapsed
    return f"{collapsed[: char_budget - 3].rstrip()}..."


def _select_context_chunks(context_chunks: list[str], max_context_tokens: int) -> list[str]:
    if not context_chunks:
        return []

    remaining = max(512, max_context_tokens)
    selected: list[str] = []
    for chunk in context_chunks:
        cost = _approx_tokens(chunk)
        if cost <= remaining:
            selected.append(chunk)
            remaining -= cost
            continue
        if not selected or remaining > 120:
            selected.append(_truncate_text_to_tokens(chunk, remaining))
        break
    return selected


def _role_prompt(role: str) -> str:
    normalized_role = canonical_role(role)
    if normalized_role == "admin":
        return ADMIN_SYSTEM_PROMPT
    if normalized_role == "control_room_officer":
        return CONTROL_ROOM_SYSTEM_PROMPT
    return PUBLIC_SYSTEM_PROMPT


def _normalize_history(history: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in history[-MAX_HISTORY_MESSAGES:]:
        role = str(item.get("role") or "").strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = " ".join(str(item.get("content") or "").split())
        if not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def _build_user_prompt(context_chunks: list[str], question: str) -> str:
    context_block = "\n\n".join(f"{index + 1}. {chunk}" for index, chunk in enumerate(context_chunks))
    if not context_block:
        context_block = "No retrieved context was available."
    return (
        "Use only the retrieved context below when answering. "
        "If the context is incomplete, say exactly what is missing.\n\n"
        f"Retrieved context:\n{context_block}\n\n"
        f"Question: {question.strip()}"
    )


def _openai_messages(
    context_chunks: list[str],
    conversation_history: list[dict[str, Any]],
    question: str,
    role: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": _role_prompt(role)}]
    messages.extend(_normalize_history(conversation_history))
    messages.append({"role": "user", "content": _build_user_prompt(context_chunks, question)})
    return messages


def _extract_body(chunk: str) -> tuple[str | None, str]:
    match = SOURCE_PATTERN.match(chunk)
    if not match:
        cleaned = " ".join(chunk.split())
        return None, cleaned
    label = f"{match.group('chunk_type')}:{match.group('source_id')}"
    body = " ".join(match.group("body").split())
    return label, body


def _fallback_intro(role: str, has_context: bool) -> str:
    normalized_role = canonical_role(role)
    if not has_context:
        if normalized_role == "control_room_officer":
            return "I could not find enough indexed operational context to answer that safely right now."
        if normalized_role == "admin":
            return "I could not find enough indexed platform context to answer that safely right now."
        return "I could not find enough indexed public context to answer that safely right now."
    if normalized_role == "control_room_officer":
        return "Here is the strongest indexed operational context I found for that question."
    if normalized_role == "admin":
        return "Here is the strongest indexed platform context I found for that question."
    return "Here is the strongest indexed public context I found for that question."


def _fallback_tail(role: str) -> str:
    normalized_role = canonical_role(role)
    if normalized_role == "admin":
        return "This answer is grounded only in the currently indexed admin and operational records."
    if normalized_role == "control_room_officer":
        return "This answer is grounded only in the currently indexed operational records."
    return "This answer is grounded only in the currently indexed public records."


def _compose_fallback_answer(context_chunks: list[str], question: str, role: str) -> str:
    selected = _select_context_chunks(context_chunks, get_settings().rag_max_context_tokens)[:FALLBACK_CHUNK_LIMIT]
    lines = [_fallback_intro(role, bool(selected))]
    if question.strip():
        lines.append("")
        lines.append(f"Question understood as: {question.strip()}")
    if selected:
        lines.append("")
        lines.append("Relevant indexed context:")
        for chunk in selected:
            label, body = _extract_body(chunk)
            if label:
                lines.append(f"- {body} [{label}]")
            else:
                lines.append(f"- {body}")
    lines.append("")
    lines.append(_fallback_tail(role))
    return "\n".join(lines).strip()


async def _stream_fallback_answer(answer: str) -> AsyncGenerator[str, None]:
    for token in TOKEN_SPLIT_PATTERN.findall(answer):
        yield token
        await asyncio.sleep(0)


async def _stream_openai_compatible(
    provider: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    config = PROVIDER_CONFIGS[provider]
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.2,
    }
    timeout = httpx.Timeout(connect=10.0, read=None, write=30.0, pool=10.0)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", f"{config['base_url']}/chat/completions", headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                payload = json.loads(data)
                choices = payload.get("choices") or []
                delta = dict(choices[0].get("delta") or {}) if choices else {}
                content = delta.get("content")
                if isinstance(content, str) and content:
                    yield content


def _stream_gemini_sync(api_key: str, model: str, prompt: str) -> list[str]:
    if genai is None:
        raise RuntimeError("google-generativeai dependency is not installed")
    genai.configure(api_key=api_key)
    model_client = genai.GenerativeModel(model)
    chunks: list[str] = []
    for chunk in model_client.generate_content(prompt, stream=True):
        text = getattr(chunk, "text", None)
        if isinstance(text, str) and text:
            chunks.append(text)
    return chunks


async def _stream_gemini(
    api_key: str,
    model: str,
    context_chunks: list[str],
    conversation_history: list[dict[str, Any]],
    question: str,
    role: str,
) -> AsyncGenerator[str, None]:
    history_lines = []
    for item in _normalize_history(conversation_history):
        history_lines.append(f"{item['role'].title()}: {item['content']}")
    history_text = "\n".join(history_lines) if history_lines else "No prior history."
    prompt = (
        f"System instruction:\n{_role_prompt(role)}\n\n"
        f"Conversation history:\n{history_text}\n\n"
        f"{_build_user_prompt(context_chunks, question)}"
    )
    model_candidates = [model]
    for fallback_model in PROVIDER_CONFIGS["gemini"].get("fallback_models", ()):  # type: ignore[union-attr]
        if fallback_model not in model_candidates:
            model_candidates.append(str(fallback_model))

    last_error: Exception | None = None
    for candidate in model_candidates:
        try:
            chunks = await asyncio.to_thread(_stream_gemini_sync, api_key, candidate, prompt)
            for chunk in chunks:
                yield chunk
                await asyncio.sleep(0)
            return
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini RAG generation failed for model %s: %s", candidate, exc)

    if last_error is not None:
        raise last_error

async def _stream_anthropic(
    api_key: str,
    model: str,
    context_chunks: list[str],
    conversation_history: list[dict[str, Any]],
    question: str,
    role: str,
) -> AsyncGenerator[str, None]:
    if anthropic is None:
        raise RuntimeError("anthropic dependency is not installed")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    messages = _normalize_history(conversation_history)
    messages.append({"role": "user", "content": _build_user_prompt(context_chunks, question)})

    async with client.messages.stream(
        model=model,
        max_tokens=1200,
        system=_role_prompt(role),
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            if text:
                yield text


def _resolve_llm_settings() -> tuple[str, str | None, str]:
    settings = get_settings()
    configured_provider = (settings.rag_llm_provider or "").strip().lower()
    embedding_provider = (settings.rag_embedding_provider or "").strip().lower()
    provider = configured_provider or "gemini"

    api_key = settings.rag_llm_api_key
    if not api_key and embedding_provider in PROVIDER_CONFIGS:
        provider = embedding_provider
        api_key = settings.rag_embedding_api_key

    config = PROVIDER_CONFIGS.get(provider)
    if config is None:
        logger.warning("Unsupported RAG_LLM_PROVIDER=%s; using gemini fallback provider", provider)
        provider = "gemini"
        config = PROVIDER_CONFIGS[provider]

    model = settings.rag_llm_model or str(config["default_model"])
    return provider, api_key, model


async def stream_llm_response(
    context_chunks: list[str],
    conversation_history: list[dict[str, Any]],
    question: str,
    role: str,
) -> AsyncGenerator[str, None]:
    settings = get_settings()
    provider, api_key, model = _resolve_llm_settings()
    selected_context = _select_context_chunks(context_chunks, settings.rag_max_context_tokens)

    if not api_key:
        logger.warning("RAG LLM fallback used because no API key is configured for provider %s", provider)
        async for token in _stream_fallback_answer(_compose_fallback_answer(selected_context, question, role)):
            yield token
        return

    try:
        if provider in {"openai", "deepseek", "groq", "mistral", "qwen"}:
            async for token in _stream_openai_compatible(
                provider,
                api_key,
                model,
                _openai_messages(selected_context, conversation_history, question, role),
            ):
                yield token
            return
        if provider == "gemini":
            async for token in _stream_gemini(api_key, model, selected_context, conversation_history, question, role):
                yield token
            return
        if provider == "anthropic":
            async for token in _stream_anthropic(api_key, model, selected_context, conversation_history, question, role):
                yield token
            return
    except Exception:
        logger.exception("RAG LLM provider %s failed with model %s; using grounded fallback answer", provider, model)

    async for token in _stream_fallback_answer(_compose_fallback_answer(selected_context, question, role)):
        yield token
