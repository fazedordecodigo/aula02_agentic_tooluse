from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    """Documento mínimo para RAG didático.

    Mantém a mesma ideia de `langchain_core.documents.Document`: conteúdo + metadados.
    O projeto usa esta classe no fallback offline para permitir testes sem dependências externas.
    """

    page_content: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RetrievedContext:
    """Resultado padronizado da ferramenta de recuperação."""

    query: str
    documents: list[Document]
    serialized_context: str
    scores: list[float]


@dataclass(frozen=True)
class ToolResult:
    """Resultado padronizado de ferramenta de domínio."""

    name: str
    ok: bool
    data: dict[str, Any]
    error: str | None = None


@dataclass
class AgentState:
    """Estado explícito do agente para rastreabilidade e avaliação."""

    user_input: str
    customer_id: str | None = None
    route: str = ""
    confidence: float = 0.0
    blocked: bool = False
    needs_human: bool = False
    question_for_retrieval: str = ""
    retrieved_context: RetrievedContext | None = None
    tool_results: list[ToolResult] = field(default_factory=list)
    final_answer: str = ""
    sources: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
