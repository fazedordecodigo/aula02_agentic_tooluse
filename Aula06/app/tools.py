from __future__ import annotations

from typing import Any

from app.costing import estimate_ai_cost_from_text
from app.rag import retrieve_documents, to_source_documents


def build_langchain_tools(vector_store: object, top_k: int) -> list[object]:
    """Exemplo de ferramentas LangChain reais para evolução do handson.

    A implementação principal usa LangGraph com nós explícitos. Este factory mostra
    como transformar as mesmas capacidades em tools LangChain sem mocks.
    """
    from langchain_core.tools import tool

    @tool
    def estimar_custo_ia(pergunta: str) -> dict[str, Any]:
        """Estima custo mensal de IA a partir de texto contendo chamadas e tokens."""
        return estimate_ai_cost_from_text(pergunta)

    @tool
    def buscar_base_conhecimento(pergunta: str) -> list[dict[str, Any]]:
        """Busca trechos relevantes na base vetorial PGVector."""
        docs = retrieve_documents(vector_store, pergunta, top_k=top_k)
        return [source.model_dump() for source in to_source_documents(docs)]

    return [estimar_custo_ia, buscar_base_conhecimento]
