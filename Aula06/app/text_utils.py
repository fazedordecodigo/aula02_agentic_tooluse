from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_text(text: str) -> str:
    """Normaliza texto para comparações determinísticas simples."""
    without_accents = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents.lower()).strip()


def trim_text(text: str, max_chars: int = 700) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def ai_message_to_text(message: Any) -> str:
    """Extrai texto de AIMessage em formatos Gemini 2.x e Gemini 3.x.

    Modelos Gemini 3 podem retornar blocos de conteúdo; modelos anteriores tendem
    a retornar string. A propriedade `.text`, quando presente, é preferida.
    """
    text_attr = getattr(message, "text", None)
    if isinstance(text_attr, str) and text_attr.strip():
        return text_attr.strip()

    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                value = block.get("text") or block.get("content")
                if isinstance(value, str):
                    parts.append(value)
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts).strip()

    return str(content).strip()
