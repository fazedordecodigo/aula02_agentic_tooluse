"""Google Gemini model factory for the demo."""

from __future__ import annotations

import os
from typing import Any

DEFAULT_GOOGLE_MODEL = "gemini-2.5-flash"


def build_google_llm(model_name: str | None = None) -> Any:
    """Build a Google Gemini chat model through LangChain.

    The function is isolated so tests can inject a fake model without requiring
    network calls or Google credentials.
    """
    try:
        from langchain_google_genai import (  # pylint: disable=import-outside-toplevel
            ChatGoogleGenerativeAI,
            HarmBlockThreshold,
            HarmCategory,
        )
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Instale as dependências com: "
            "pip install -e '.[dev]' ou pip install langchain-google-genai"
        ) from exc

    selected_model = model_name or os.getenv("GOOGLE_MODEL", DEFAULT_GOOGLE_MODEL)
    return ChatGoogleGenerativeAI(
        model=selected_model,
        temperature=0,
        max_retries=2,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: (
                HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: (
                HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            HarmCategory.HARM_CATEGORY_HARASSMENT: (
                HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: (
                HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            ),
        },
    )
