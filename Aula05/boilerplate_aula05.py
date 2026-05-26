"""
Boilerplate direto ao ponto — Aula 5: RAG aplicado a agentes.

Objetivo do exercício:
1. Completar a base documental.
2. Implementar retrieve_context.
3. Adicionar verificação de suficiência.
4. Incrementar o exercício anterior: status SIN-1001 + SLA + ticket com fontes RAG.

Rodar:
    python boilerplate_aula05.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    page_content: str
    metadata: dict[str, Any]


@dataclass
class State:
    user_input: str
    customer_id: str | None = None
    route: str = ""
    retrieved_docs: list[Document] = field(default_factory=list)
    final_answer: str = ""
    trace: list[str] = field(default_factory=list)


DOCS = [
    Document(
        page_content="TODO: adicione aqui uma regra de cobertura, franquia ou SLA.",
        metadata={"source_id": "KB-TODO-001", "domain": "apolice"},
    )
]


def retrieve_context(query: str, k: int = 3) -> list[Document]:
    """TODO: implemente busca lexical simples ou conecte LangChain VectorStore."""
    raise NotImplementedError


def route(state: State) -> State:
    """TODO: defina rotas: apolice_rag, sinistro_rag, fraude_rag, humano."""
    raise NotImplementedError


def answer(state: State) -> State:
    """TODO: responda usando apenas documentos recuperados e cite source_id."""
    raise NotImplementedError


def run(user_input: str, customer_id: str | None = None) -> State:
    state = State(user_input=user_input, customer_id=customer_id)
    for step in [route, answer]:
        state = step(state)
    return state


if __name__ == "__main__":
    print(run("Qual o status do sinistro SIN-1001? Calcule SLA urgente via whatsapp e abrir ticket", "C001"))
