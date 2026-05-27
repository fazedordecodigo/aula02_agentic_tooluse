from __future__ import annotations

from functools import lru_cache
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do serviço.

    O projeto aceita GOOGLE_API_KEY ou GEMINI_API_KEY porque integrações e exemplos
    oficiais usam ambas as nomenclaturas em diferentes contextos.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    )
    gemini_chat_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_CHAT_MODEL")
    gemini_embedding_model: str = Field(default="gemini-embedding-2", alias="GEMINI_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS")

    database_url: str = Field(
        default="postgresql+psycopg://langchain:langchain@localhost:6024/langchain",
        alias="DATABASE_URL",
    )
    vector_collection_name: str = Field(default="porto_ai_experts_kb", alias="VECTOR_COLLECTION_NAME")

    rag_top_k: int = Field(default=4, alias="RAG_TOP_K", ge=1, le=20)
    chunk_size: int = Field(default=900, alias="CHUNK_SIZE", ge=200, le=4000)
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP", ge=0, le=1000)
    max_context_chars: int = Field(default=9000, alias="MAX_CONTEXT_CHARS", ge=1000)
    router_confidence_threshold: float = Field(default=0.55, alias="ROUTER_CONFIDENCE_THRESHOLD", ge=0.0, le=1.0)

    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    def require_api_key(self) -> str:
        if not self.google_api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY ou GEMINI_API_KEY não configurada. "
                "Defina uma chave válida no .env antes de chamar LLM/embeddings."
            )
        return self.google_api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
