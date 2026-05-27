from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException

from app.graph import build_agent_graph
from app.providers import get_runtime_services
from app.rag import index_documents, load_seed_documents
from app.schemas import AskRequest, AskResponse, HealthResponse, IngestRequest, IngestResponse, SourceDocument

app = FastAPI(
    title="Aula 6 — Porto AI Experts: Agente Gemini + RAG",
    version="1.0.0",
    description="Hands-on real com Gemini, LangGraph, LangChain, RAG e PGVector.",
)


@lru_cache(maxsize=1)
def get_agent_graph() -> object:
    services = get_runtime_services()
    return build_agent_graph(services)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="aula06-agent-rag-gemini")


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    services = get_runtime_services()
    docs = list(request.documents)
    if request.load_seed:
        docs.extend(load_seed_documents())

    if not docs:
        raise HTTPException(status_code=400, detail="Informe documents ou load_seed=true.")

    try:
        indexed = index_documents(
            services.vector_store,
            docs,
            chunk_size=services.settings.chunk_size,
            chunk_overlap=services.settings.chunk_overlap,
        )
    except Exception as exc:  # noqa: BLE001 - responde erro operacional da ingestão
        raise HTTPException(status_code=500, detail=f"Falha na ingestão: {exc}") from exc

    return IngestResponse(
        indexed_chunks=indexed,
        document_count=len(docs),
        collection_name=services.settings.vector_collection_name,
    )


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    graph = get_agent_graph()
    try:
        state = graph.invoke(
            {
                "question": request.question,
                "customer_id": request.customer_id,
                "trace": [],
            }
        )
    except Exception as exc:  # noqa: BLE001 - API deve explicar erro operacional
        raise HTTPException(status_code=500, detail=f"Falha ao executar agente: {exc}") from exc

    sources = [SourceDocument.model_validate(item) for item in state.get("sources", [])]
    return AskResponse(
        answer=state.get("answer", ""),
        route=state.get("route", "human"),
        confidence=float(state.get("confidence", 0.0)),
        risk=state.get("risk", "medio"),
        sources=sources,
        trace=state.get("trace", []) if request.include_trace else [],
    )
