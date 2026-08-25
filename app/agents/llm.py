from __future__ import annotations

import json

from langchain_ollama import ChatOllama

from ..config import get_settings


def get_llm(temperature: float = 0.0) -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=temperature,
        format="json",
    )


def ask_json(prompt: str) -> dict:
    """Send a prompt to the local DeepSeek-Coder model and parse its JSON reply."""
    llm = get_llm()
    response = llm.invoke(prompt)
    return json.loads(response.content)
