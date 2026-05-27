from __future__ import annotations

from typing import Any, Literal, TypedDict

from app.costing import estimate_ai_cost_from_text
from app.guardrails import check_guardrails
from app.rag import format_context, retrieve_documents, to_source_documents
from app.schemas import RouteDecision
from app.text_utils import ai_message_to_text, normalize_text


class AgentState(TypedDict, total=False):
    question: str
    customer_id: str | None
    route: str
    confidence: float
    risk: str
    rationale: str
    answer: str
    context: str
    sources: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    blocked_reason: str | None
    needs_human: bool
    error: str | None


def add_trace(state: AgentState, step: str, **payload: Any) -> list[dict[str, Any]]:
    trace = list(state.get("trace", []))
    trace.append({"step": step, **payload})
    return trace


def _fallback_route(question: str, threshold: float) -> RouteDecision:
    """Fallback determinístico caso a chamada estruturada do roteador falhe."""
    q = normalize_text(question)
    if any(term in q for term in ["custo", "token", "finops", "latencia", "estimativa"]):
        return RouteDecision(route="finops", confidence=max(threshold, 0.6), risk="baixo", rationale="Fallback por termos FinOps.")
    if any(term in q for term in ["humano", "atendente", "ouvidoria", "reclamacao"]):
        return RouteDecision(route="human", confidence=0.7, risk="medio", rationale="Fallback por pedido explícito de humano.")
    return RouteDecision(route="rag", confidence=max(threshold, 0.6), risk="baixo", rationale="Fallback para consulta RAG geral.")


def build_agent_graph(services: object) -> object:
    """Constrói grafo LangGraph com dependências reais injetadas."""
    from langchain_core.prompts import ChatPromptTemplate
    from langgraph.graph import END, START, StateGraph

    settings = services.settings
    llm = services.llm
    vector_store = services.vector_store

    router_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Você é um roteador operacional para um agente corporativo da Porto. "
                "Escolha exatamente uma rota: rag, finops, human ou blocked. "
                "Use rag para perguntas técnicas, arquitetura agentic, LangChain, LangGraph, RAG, guardrails e conteúdo do curso. "
                "Use finops para custo, tokens, latência, consumo e otimização. "
                "Use human para reclamações, baixa clareza, decisão sensível ou solicitação que exige pessoa. "
                "Use blocked apenas para pedidos perigosos ou credenciais. "
                "A justificativa deve ser curta e auditável; não revele raciocínio interno.",
            ),
            (
                "human",
                "Pergunta: {question}\nCustomer ID: {customer_id}\nRetorne a decisão estruturada.",
            ),
        ]
    )
    structured_router = llm.with_structured_output(RouteDecision)

    answer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Você é o assistente técnico do hands-on AI Experts Porto. "
                "Responda em português, de forma objetiva, usando somente o contexto recuperado e deixando claro quando faltar evidência. "
                "Inclua uma seção curta 'Fontes usadas' com os títulos/fontes presentes no contexto. "
                "Não invente números, políticas internas, protocolos ou dados de cliente.",
            ),
            (
                "human",
                "Contexto recuperado:\n{context}\n\nPergunta do usuário:\n{question}\n\nResposta:",
            ),
        ]
    )

    def guardrail_node(state: AgentState) -> AgentState:
        result = check_guardrails(state["question"])
        if not result.allowed:
            return {
                "route": "blocked",
                "risk": "alto",
                "confidence": 1.0,
                "blocked_reason": result.reason,
                "trace": add_trace(
                    state,
                    "guardrail",
                    allowed=False,
                    reason=result.reason,
                    matched_pattern=result.matched_pattern,
                ),
            }
        return {
            "blocked_reason": None,
            "trace": add_trace(state, "guardrail", allowed=True),
        }

    def blocked_node(state: AgentState) -> AgentState:
        reason = state.get("blocked_reason") or "Solicitação bloqueada por política de segurança."
        return {
            "answer": (
                "Não posso atender essa solicitação porque ela envolve risco de segurança, credenciais, "
                f"dados sensíveis ou tentativa de burlar controles. Motivo: {reason} "
                "Reformule a pergunta sem segredos, dados pessoais ou comandos de bypass."
            ),
            "sources": [],
            "trace": add_trace(state, "blocked_response", reason=reason),
        }

    def route_node(state: AgentState) -> AgentState:
        try:
            decision_raw = (router_prompt | structured_router).invoke(
                {"question": state["question"], "customer_id": state.get("customer_id") or "não informado"}
            )
            decision = decision_raw if isinstance(decision_raw, RouteDecision) else RouteDecision.model_validate(decision_raw)
        except Exception as exc:  # noqa: BLE001 - fallback operacional explícito
            decision = _fallback_route(state["question"], settings.router_confidence_threshold)
            return {
                "route": decision.route,
                "confidence": decision.confidence,
                "risk": decision.risk,
                "rationale": decision.rationale,
                "trace": add_trace(state, "router", mode="fallback", error=str(exc), decision=decision.model_dump()),
            }

        route = decision.route
        if decision.confidence < settings.router_confidence_threshold and route not in {"blocked", "human"}:
            route = "human"

        return {
            "route": route,
            "confidence": decision.confidence,
            "risk": decision.risk,
            "rationale": decision.rationale,
            "trace": add_trace(state, "router", mode="llm_structured", decision=decision.model_dump(), selected_route=route),
        }

    def retrieve_node(state: AgentState) -> AgentState:
        docs = retrieve_documents(vector_store, state["question"], settings.rag_top_k)
        context = format_context(docs, settings.max_context_chars)
        sources = [source.model_dump() for source in to_source_documents(docs)]
        return {
            "context": context,
            "sources": sources,
            "trace": add_trace(state, "retrieve", k=settings.rag_top_k, returned=len(docs)),
        }

    def rag_answer_node(state: AgentState) -> AgentState:
        if not state.get("context"):
            return {
                "answer": "Não encontrei contexto suficiente na base de conhecimento para responder com segurança.",
                "needs_human": True,
                "trace": add_trace(state, "rag_answer", generated=False, reason="empty_context"),
            }
        message = (answer_prompt | llm).invoke({"context": state["context"], "question": state["question"]})
        return {
            "answer": ai_message_to_text(message),
            "trace": add_trace(state, "rag_answer", generated=True),
        }

    def finops_node(state: AgentState) -> AgentState:
        estimate = estimate_ai_cost_from_text(state["question"])
        answer = (
            "Estimativa FinOps didática:\n"
            f"- Chamadas/mês: {estimate['monthly_requests']}\n"
            f"- Tokens médios de entrada: {estimate['avg_input_tokens']}\n"
            f"- Tokens médios de saída: {estimate['avg_output_tokens']}\n"
            f"- Custo entrada: US$ {estimate['input_cost_usd']}\n"
            f"- Custo saída: US$ {estimate['output_cost_usd']}\n"
            f"- Custo total estimado: US$ {estimate['total_cost_usd']}\n\n"
            "Próximos controles recomendados: cache para perguntas repetidas, limite de tokens, roteamento por modelo, "
            "métricas de custo por rota e alertas por orçamento."
        )
        return {
            "answer": answer,
            "sources": [],
            "trace": add_trace(state, "finops", estimate=estimate),
        }

    def verify_node(state: AgentState) -> AgentState:
        answer = state.get("answer", "")
        needs_human = bool(state.get("needs_human"))
        if not answer.strip():
            needs_human = True
        if state.get("route") == "rag" and not state.get("sources"):
            needs_human = True
        return {
            "needs_human": needs_human,
            "trace": add_trace(state, "verify", ok=not needs_human),
        }

    def human_node(state: AgentState) -> AgentState:
        reason = state.get("rationale") or state.get("error") or "Baixa confiança, falta de evidência ou necessidade de decisão humana."
        return {
            "route": "human",
            "risk": state.get("risk", "medio"),
            "answer": (
                "Este caso deve ser encaminhado para avaliação humana antes de qualquer ação operacional.\n"
                f"Motivo: {reason}\n"
                "Sugestão de handoff: envie a pergunta, o customer_id se existir, a rota tentada, fontes recuperadas e trace técnico."
            ),
            "trace": add_trace(state, "human_fallback", reason=reason),
        }

    def after_guardrail(state: AgentState) -> Literal["blocked", "route"]:
        return "blocked" if state.get("route") == "blocked" else "route"

    def after_route(state: AgentState) -> Literal["blocked", "retrieve", "finops", "human"]:
        route = state.get("route", "rag")
        if route == "blocked":
            return "blocked"
        if route == "finops":
            return "finops"
        if route == "human":
            return "human"
        return "retrieve"

    def after_verify(state: AgentState) -> Literal["human", "end"]:
        return "human" if state.get("needs_human") else "end"

    builder = StateGraph(AgentState)
    builder.add_node("guardrail", guardrail_node)
    builder.add_node("blocked", blocked_node)
    builder.add_node("route", route_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("rag_answer", rag_answer_node)
    builder.add_node("finops", finops_node)
    builder.add_node("verify", verify_node)
    builder.add_node("human", human_node)

    builder.add_edge(START, "guardrail")
    builder.add_conditional_edges("guardrail", after_guardrail, {"blocked": "blocked", "route": "route"})
    builder.add_conditional_edges(
        "route",
        after_route,
        {"blocked": "blocked", "retrieve": "retrieve", "finops": "finops", "human": "human"},
    )
    builder.add_edge("retrieve", "rag_answer")
    builder.add_edge("rag_answer", "verify")
    builder.add_edge("finops", "verify")
    builder.add_conditional_edges("verify", after_verify, {"human": "human", "end": END})
    builder.add_edge("blocked", END)
    builder.add_edge("human", END)

    return builder.compile()
