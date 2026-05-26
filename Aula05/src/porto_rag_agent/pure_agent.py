from __future__ import annotations

from .domain_tools import (
    abrir_ticket,
    calcular_prazo_sla,
    check_fraud,
    consultar_status_sinistro,
    detectar_canal,
    detectar_prioridade,
    detectar_sinistro,
)
from .knowledge_base import build_knowledge_base
from .models import AgentState, ToolResult
from .text_utils import contains_any, normalize_text
from .vector_store import SimpleVectorStore


DANGEROUS_TERMS = [
    "cpf",
    "senha",
    "cartao",
    "dados pessoais",
    "api key",
    "token secreto",
    "ignore as instrucoes",
    "ignore instrucoes",
    "desative o guardrail",
    "revele segredo",
]


def guardrail_node(state: AgentState) -> AgentState:
    if contains_any(state.user_input, DANGEROUS_TERMS):
        state.blocked = True
        state.route = "bloqueado"
        state.trace.append("guardrail=blocked")
    else:
        state.trace.append("guardrail=ok")
    return state


def route_node(state: AgentState) -> AgentState:
    if state.blocked:
        return state

    msg = normalize_text(state.user_input)
    scores = {
        "fraude_rag": sum(term in msg for term in ["fraude", "golpe", "conta invadida", "login incomum"]),
        "sinistro_rag": sum(term in msg for term in ["sinistro", "vistoria", "andamento", "sla", "ticket", "chamado"]),
        "apolice_rag": sum(term in msg for term in ["cobertura", "cobre", "franquia", "seguro auto", "guincho", "apolice"]),
        "geral_rag": 1,
    }
    route, score = max(scores.items(), key=lambda item: item[1])
    total = max(sum(scores.values()), 1)
    state.route = route
    state.confidence = round(score / total, 2)
    state.question_for_retrieval = build_retrieval_query(state)
    state.trace.append(f"route={state.route}; confidence={state.confidence}; scores={scores}")
    return state


def build_retrieval_query(state: AgentState) -> str:
    """Transforma solicitação operacional em consulta documental melhor para RAG."""
    msg = normalize_text(state.user_input)
    if any(t in msg for t in ["sla", "prazo", "urgente"]):
        return f"matriz SLA {detectar_prioridade(state.user_input)} {detectar_canal(state.user_input)} sinistro"
    if any(t in msg for t in ["franquia", "cobertura", "guincho", "seguro auto"]):
        return f"cobertura franquia seguro auto guincho {state.user_input}"
    if any(t in msg for t in ["fraude", "golpe", "conta invadida", "login incomum"]):
        return f"procedimento suspeita fraude login incomum conta invadida {state.user_input}"
    if "sinistro" in msg:
        numero = detectar_sinistro(state.user_input) or ""
        return f"procedimento sinistro {numero} status vistoria próximos passos"
    return state.user_input


def domain_for_route(route: str) -> str | None:
    return {
        "sinistro_rag": None,  # sem filtro para permitir recuperar procedimento + SLA
        "apolice_rag": "apolice",
        "fraude_rag": "fraude",
        "geral_rag": None,
    }.get(route)


def retrieve_node(state: AgentState, vector_store: SimpleVectorStore) -> AgentState:
    if state.blocked:
        return state
    context = vector_store.retrieve(
        query=state.question_for_retrieval or state.user_input,
        k=3,
        domain=domain_for_route(state.route),
        min_score=0.03,
    )
    state.retrieved_context = context
    state.sources = [str(doc.metadata.get("source_id")) for doc in context.documents]
    state.trace.append(f"retrieved={len(context.documents)}; sources={state.sources}; scores={context.scores}")
    return state


def business_tools_node(state: AgentState) -> AgentState:
    if state.blocked:
        return state

    msg = normalize_text(state.user_input)
    if state.route == "sinistro_rag":
        numero = detectar_sinistro(state.user_input)
        if numero:
            state.tool_results.append(consultar_status_sinistro(numero))
        if any(term in msg for term in ["sla", "prazo"]):
            state.tool_results.append(calcular_prazo_sla(detectar_prioridade(state.user_input), detectar_canal(state.user_input)))
        if any(term in msg for term in ["abrir ticket", "criar ticket", "registrar chamado", "ticket"]):
            state.tool_results.append(abrir_ticket("sinistros", state.user_input[:180], detectar_prioridade(state.user_input)))
    elif state.route == "fraude_rag":
        state.tool_results.append(check_fraud(state.customer_id))

    state.trace.append("tools=" + ",".join(result.name for result in state.tool_results) if state.tool_results else "tools=none")
    return state


def verify_node(state: AgentState) -> AgentState:
    if state.blocked:
        return state

    if not state.retrieved_context or len(state.retrieved_context.documents) == 0:
        state.needs_human = True
        state.trace.append("verification=failed:no_context")
        return state

    failures = [result for result in state.tool_results if not result.ok]
    if failures:
        state.needs_human = True
        reason = failures[0].error or "falha de ferramenta"
        state.tool_results.append(abrir_ticket("atendimento", reason, "alta"))
        state.trace.append(f"verification=failed:{reason}; escalated=true")
        return state

    state.trace.append("verification=ok")
    return state


def answer_node(state: AgentState) -> AgentState:
    if state.blocked:
        state.final_answer = (
            "Não posso atender essa solicitação porque ela envolve dado sensível, segredo, "
            "credencial ou tentativa de burlar instruções. Reformule sem dados sensíveis."
        )
        return state

    if state.needs_human:
        ticket = next((r for r in reversed(state.tool_results) if r.name == "abrir_ticket" and r.ok), None)
        protocolo = ticket.data["protocolo"] if ticket else "HUM-PENDENTE"
        state.final_answer = (
            f"Não encontrei contexto suficiente ou uma ferramenta retornou falha. Encaminhei para humano. "
            f"Protocolo: {protocolo}. Fontes avaliadas: {', '.join(state.sources) or 'nenhuma'}."
        )
        return state

    context_summary = summarize_context(state)
    tool_summary = summarize_tools(state.tool_results)
    fontes = ", ".join(state.sources) if state.sources else "sem fonte recuperada"
    state.final_answer = (
        f"Resposta fundamentada por RAG:\n"
        f"{context_summary}\n"
        f"{tool_summary}"
        f"Fontes: {fontes}.\n"
        "Observação: conteúdo recuperado foi tratado como dado de apoio; decisões operacionais vieram de ferramentas mockadas."
    )
    return state


def summarize_context(state: AgentState) -> str:
    if not state.retrieved_context or not state.retrieved_context.documents:
        return "- Não houve documentos relevantes recuperados.\n"
    bullets = []
    for doc in state.retrieved_context.documents[:2]:
        source = doc.metadata.get("source_id")
        title = doc.metadata.get("title")
        excerpt = doc.page_content[:220].strip()
        bullets.append(f"- Fonte {source} ({title}): {excerpt}...")
    return "\n".join(bullets) + "\n"


def summarize_tools(results: list[ToolResult]) -> str:
    if not results:
        return "- Nenhuma ferramenta operacional adicional foi necessária.\n"
    lines: list[str] = []
    for result in results:
        if not result.ok:
            lines.append(f"- {result.name}: falha — {result.error}.")
            continue
        if result.name == "consultar_status_sinistro":
            data = result.data
            lines.append(
                f"- Sinistro {data['numero_sinistro']}: status '{data['status']}', etapa '{data['etapa']}', previsão {data['previsao']}."
            )
        elif result.name == "calcular_prazo_sla":
            data = result.data
            lines.append(f"- SLA estimado: {data['sla_legivel']} para criticidade {data['criticidade']} via {data['canal']}.")
        elif result.name == "abrir_ticket":
            data = result.data
            lines.append(f"- Ticket criado: {data['protocolo']} | área: {data['area']} | prioridade: {data['prioridade']}.")
        elif result.name == "check_fraud":
            signals = ", ".join(result.data["signals"]) or "sem sinais adicionais na base mockada"
            lines.append(f"- Fraude: risco {result.data['risk']}; sinais: {signals}; recomendar validação reforçada.")
        else:
            lines.append(f"- {result.name}: {result.data}")
    return "\n".join(lines) + "\n"


class PortoRAGAgent:
    def __init__(self, vector_store: SimpleVectorStore) -> None:
        self.vector_store = vector_store

    def run(self, user_input: str, customer_id: str | None = None) -> AgentState:
        state = AgentState(user_input=user_input, customer_id=customer_id)
        state = guardrail_node(state)
        state = route_node(state)
        state = retrieve_node(state, self.vector_store)
        state = business_tools_node(state)
        state = verify_node(state)
        state = answer_node(state)
        return state


def build_default_agent() -> PortoRAGAgent:
    return PortoRAGAgent(SimpleVectorStore(build_knowledge_base()))


def run_agent(user_input: str, customer_id: str | None = None) -> AgentState:
    return build_default_agent().run(user_input=user_input, customer_id=customer_id)
