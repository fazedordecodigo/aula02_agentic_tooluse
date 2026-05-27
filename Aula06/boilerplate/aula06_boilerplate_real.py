"""Boilerplate direto ao ponto para o hands-on real da Aula 6.

Uso:
    export GOOGLE_API_KEY="..."
    export DATABASE_URL="postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
    python boilerplate/aula06_boilerplate_real.py
"""
from __future__ import annotations

from app.graph import build_agent_graph
from app.providers import get_runtime_services
from app.rag import index_documents, load_seed_documents


def main() -> None:
    services = get_runtime_services()

    # 1) Ingestão real: chunks + embeddings Gemini + PGVector.
    docs = load_seed_documents()
    chunks = index_documents(
        services.vector_store,
        docs,
        chunk_size=services.settings.chunk_size,
        chunk_overlap=services.settings.chunk_overlap,
    )
    print(f"Chunks indexados: {chunks}")

    # 2) Execução real: LangGraph + Gemini + retriever PGVector.
    graph = build_agent_graph(services)
    state = graph.invoke(
        {
            "question": "Quais guardrails mínimos devo implementar em um agente com RAG?",
            "customer_id": "LAB-001",
            "trace": [],
        }
    )
    print("\nResposta:\n", state["answer"])
    print("\nRota:", state.get("route"), "Confiança:", state.get("confidence"))
    print("\nFontes:")
    for source in state.get("sources", []):
        print("-", source.get("source"), "|", source.get("title"))


if __name__ == "__main__":
    main()
