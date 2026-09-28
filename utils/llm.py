"""LLM gateway: deterministic mock by default, OpenRouter when enabled."""

from __future__ import annotations

import httpx

from app.config import get_settings
from utils.mock_llm import ask_llm as ask_mock_llm


def _openrouter_messages(question: str, history: list[dict]) -> list[dict]:
    messages = [
        {
            "role": "system",
            "content": "You are a concise, helpful Vietnamese AI assistant.",
        }
    ]
    messages.extend(
        {"role": turn["role"], "content": turn["content"]}
        for turn in history
        if turn.get("role") in {"user", "assistant"} and turn.get("content")
    )
    messages.append({"role": "user", "content": question})
    return messages


def ask_openrouter(question: str, history: list[dict] | None = None) -> dict:
    """Call the configured Gemini model through OpenRouter."""
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")

    response = httpx.post(
        f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "Day 12 Production Agent",
        },
        json={
            "model": settings.openrouter_model,
            "messages": _openrouter_messages(question, history or []),
            "temperature": 0.2,
            "max_tokens": 512,
            "usage": {"include": True},
        },
        timeout=60.0,
    )
    response.raise_for_status()
    payload = response.json()
    usage = payload.get("usage") or {}
    return {
        "answer": payload["choices"][0]["message"]["content"],
        "tokens_in": int(usage.get("prompt_tokens") or 0),
        "tokens_out": int(usage.get("completion_tokens") or 0),
        "cost_usd": float(usage.get("cost") or 0.0),
    }


def ask_llm(question: str, history: list[dict] | None = None) -> dict:
    """Route to OpenRouter only when explicitly enabled."""
    provider = get_settings().llm_provider.strip().lower()
    if provider == "mock":
        return ask_mock_llm(question, history)
    if provider == "openrouter":
        return ask_openrouter(question, history)
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")
