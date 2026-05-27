from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from app.embeddings import GeminiRetrievalEmbeddings
from app.settings import Settings, get_settings


@dataclass(frozen=True)
class RuntimeServices:
    settings: Settings
    llm: object
    embeddings: object
    vector_store: object


def build_llm(settings: Settings) -> object:
    """Cria ChatGoogleGenerativeAI real de forma lazy."""
    settings.require_api_key()
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key or "")

    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model,
        temperature=0.2,
        max_retries=2,
        timeout=60,
    )


def build_embeddings(settings: Settings) -> object:
    """Cria embeddings Gemini reais com dimensionalidade controlada."""
    settings.require_api_key()
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key or "")

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    inner = GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,
        output_dimensionality=settings.embedding_dimensions,
    )
    return GeminiRetrievalEmbeddings(inner)


def build_vector_store(settings: Settings, embeddings: object) -> object:
    """Cria vector store real em PostgreSQL/pgvector."""
    from langchain_postgres import PGVector

    return PGVector(
        embeddings=embeddings,
        collection_name=settings.vector_collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )


@lru_cache(maxsize=1)
def get_runtime_services() -> RuntimeServices:
    settings = get_settings()
    embeddings = build_embeddings(settings)
    llm = build_llm(settings)
    vector_store = build_vector_store(settings, embeddings)
    return RuntimeServices(
        settings=settings,
        llm=llm,
        embeddings=embeddings,
        vector_store=vector_store,
    )
