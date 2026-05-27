from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

Route = Literal["rag", "finops", "human", "blocked"]
RiskLevel = Literal["baixo", "medio", "alto"]


class RouteDecision(BaseModel):
    """Saída estruturada do roteador LLM."""

    route: Route = Field(description="Rota operacional escolhida para a pergunta.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confiança objetiva da decisão.")
    risk: RiskLevel = Field(description="Risco operacional percebido.")
    rationale: str = Field(description="Justificativa curta, auditável e sem chain-of-thought.")


class SourceDocument(BaseModel):
    source: str = Field(default="desconhecido")
    title: str | None = None
    chunk_id: str | None = None
    score: float | None = None
    preview: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=8000)
    customer_id: str | None = Field(default=None, max_length=80)
    include_trace: bool = True


class AskResponse(BaseModel):
    answer: str
    route: Route
    confidence: float
    risk: RiskLevel
    sources: list[SourceDocument] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)


class RawDocument(BaseModel):
    text: str = Field(min_length=1)
    source: str = Field(default="manual")
    title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    load_seed: bool = False
    documents: list[RawDocument] = Field(default_factory=list)


class IngestResponse(BaseModel):
    indexed_chunks: int
    document_count: int
    collection_name: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
