from __future__ import annotations

from typing import Literal, TypedDict

from .knowledge_base import build_knowledge_base
from .pure_agent import (
    answer_node,
    business_tools_node,
    guardrail_node,
    retrieve_node,
    route_node,
    verify_node,
)
from .models import AgentState
from .vector_store import SimpleVectorStore


class GraphState(TypedDict, total=False):
    user_input: str
    customer_id: str | None
    route: str
    confidence: float
    blocked: bool
    needs_human: bool
    question_for_retrieval: str
    retrieved_context: object
    tool_results: list[object]
    final_answer: str
    sources: list[str]
    trace: list[str]


def _to_agent_state(data: GraphState) -> AgentState:
    return AgentState(
        user_input=data.get("user_input", ""),
        customer_id=data.get("customer_id"),
        route=data.get("route", ""),
        confidence=float(data.get("confidence", 0.0)),
        blocked=bool(data.get("blocked", False)),
        needs_human=bool(data.get("needs_human", False)),
        question_for_retrieval=data.get("question_for_retrieval", ""),
        retrieved_context=data.get("retrieved_context"),  # type: ignore[arg-type]
        tool_results=data.get("tool_results", []),  # type: ignore[arg-type]
        final_answer=data.get("final_answer", ""),
        sources=data.get("sources", []),
        trace=data.get("trace", []),
    )


def _from_agent_state(state: AgentState) -> GraphState:
    return {
        "user_input": state.user_input,
        "customer_id": state.customer_id,
        "route": state.route,
        "confidence": state.confidence,
        "blocked": state.blocked,
        "needs_human": state.needs_human,
        "question_for_retrieval": state.question_for_retrieval,
        "retrieved_context": state.retrieved_context,
        "tool_results": state.tool_results,
        "final_answer": state.final_answer,
        "sources": state.sources,
        "trace": state.trace,
    }


def build_graph():
    """Constrói o grafo LangGraph da Aula 5.

    Requer:
        pip install -U langgraph

    O grafo usa os mesmos nós do agente puro, permitindo comparação direta entre
    implementação determinística e orquestração stateful.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:  # pragma: no cover - depende de pacotes opcionais
        raise RuntimeError("Instale langgraph para rodar esta demo: pip install -U langgraph") from exc

    vector_store = SimpleVectorStore(build_knowledge_base())

    def guardrail(data: GraphState) -> GraphState:
        return _from_agent_state(guardrail_node(_to_agent_state(data)))

    def route(data: GraphState) -> GraphState:
        return _from_agent_state(route_node(_to_agent_state(data)))

    def retrieve(data: GraphState) -> GraphState:
        return _from_agent_state(retrieve_node(_to_agent_state(data), vector_store))

    def tools(data: GraphState) -> GraphState:
        return _from_agent_state(business_tools_node(_to_agent_state(data)))

    def verify(data: GraphState) -> GraphState:
        return _from_agent_state(verify_node(_to_agent_state(data)))

    def answer(data: GraphState) -> GraphState:
        return _from_agent_state(answer_node(_to_agent_state(data)))

    def after_guardrail(data: GraphState) -> Literal["answer", "route"]:
        return "answer" if data.get("blocked") else "route"

    def after_verify(data: GraphState) -> Literal["answer"]:
        return "answer"

    builder = StateGraph(GraphState)
    builder.add_node("guardrail", guardrail)
    builder.add_node("route", route)
    builder.add_node("retrieve", retrieve)
    builder.add_node("tools", tools)
    builder.add_node("verify", verify)
    builder.add_node("answer", answer)

    builder.add_edge(START, "guardrail")
    builder.add_conditional_edges("guardrail", after_guardrail, ["answer", "route"])
    builder.add_edge("route", "retrieve")
    builder.add_edge("retrieve", "tools")
    builder.add_edge("tools", "verify")
    builder.add_conditional_edges("verify", after_verify, ["answer"])
    builder.add_edge("answer", END)

    return builder.compile()


def run_graph(user_input: str, customer_id: str | None = None) -> GraphState:
    graph = build_graph()
    return graph.invoke({"user_input": user_input, "customer_id": customer_id})
