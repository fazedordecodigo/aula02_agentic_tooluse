"""
Miniagente corporativo didático para demonstrar Arquitetura Agentic e Tool-Use.

Objetivo pedagógico:
- Mostrar o loop perceber -> planejar -> chamar ferramenta -> observar -> responder.
- Demonstrar allowlist de ferramentas, validação de argumentos, rastreabilidade e guardrails.
- Rodar 100% local, sem chave de API e sem dependências externas.

Execução:
    python src/mini_agent_porto.py

Testes:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
import json
import re
import uuid


# =========================
# 1. Contratos do agente
# =========================

@dataclass(frozen=True)
class ToolCall:
    """Pedido de execução de ferramenta feito pelo planejador."""

    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """Resultado padronizado de uma ferramenta."""

    name: str
    ok: bool
    data: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True)
class ToolDefinition:
    """Definição de uma ferramenta disponível para o agente."""

    name: str
    description: str
    required_args: tuple[str, ...]
    handler: Callable[..., dict[str, Any]]

    def validate(self, arguments: dict[str, Any]) -> None:
        missing = [arg for arg in self.required_args if arg not in arguments]
        if missing:
            raise ValueError(f"Argumentos obrigatórios ausentes para {self.name}: {', '.join(missing)}")

        extra = sorted(set(arguments) - set(self.required_args))
        if extra:
            raise ValueError(f"Argumentos não permitidos para {self.name}: {', '.join(extra)}")


@dataclass
class AgentTrace:
    """Trilha de execução para depuração, auditoria e avaliação."""

    user_input: str
    blocked: bool = False
    reason: str | None = None
    planned_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    final_answer: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "user_input": self.user_input,
                "blocked": self.blocked,
                "reason": self.reason,
                "planned_calls": [call.__dict__ for call in self.planned_calls],
                "tool_results": [result.__dict__ for result in self.tool_results],
                "final_answer": self.final_answer,
            },
            ensure_ascii=False,
            indent=2,
        )


# =========================
# 2. Dados mockados
# =========================

SINISTROS = {
    "SIN-1001": {
        "produto": "auto",
        "status": "vistoria agendada",
        "etapa": "aguardando vistoria",
        "previsao": "2 dias úteis",
    },
    "SIN-2002": {
        "produto": "residencial",
        "status": "em análise técnica",
        "etapa": "validação de cobertura",
        "previsao": "3 dias úteis",
    },
}

COBERTURAS = {
    "auto": ["colisão", "roubo e furto", "guincho", "terceiros"],
    "residencial": ["incêndio", "danos elétricos", "vendaval", "assistência 24h"],
    "vida": ["morte natural", "morte acidental", "invalidez permanente"],
}

FRANQUIAS = {
    "auto": {"valor_referencia": 1500.00, "observacao": "Franquia padrão para colisão parcial."},
    "residencial": {"valor_referencia": 800.00, "observacao": "Franquia padrão para danos elétricos."},
    "vida": {"valor_referencia": 0.00, "observacao": "Produto sem franquia na base mockada."},
}

SLA_BASE_HORAS = {
    ("alta", "whatsapp"): 4,
    ("alta", "telefone"): 6,
    ("alta", "email"): 8,
    ("media", "whatsapp"): 12,
    ("media", "telefone"): 16,
    ("media", "email"): 24,
    ("baixa", "whatsapp"): 24,
    ("baixa", "telefone"): 36,
    ("baixa", "email"): 48,
}


# =========================
# 3. Ferramentas do domínio
# =========================

def consultar_status_sinistro(numero_sinistro: str) -> dict[str, Any]:
    """Consulta status de um sinistro em base mockada."""
    sinistro = SINISTROS.get(numero_sinistro.upper())
    if not sinistro:
        return {
            "encontrado": False,
            "numero_sinistro": numero_sinistro.upper(),
            "mensagem": "Sinistro não encontrado na base mockada.",
        }
    return {"encontrado": True, "numero_sinistro": numero_sinistro.upper(), **sinistro}


def consultar_cobertura_produto(tipo_seguro: str) -> dict[str, Any]:
    """Consulta coberturas disponíveis de um produto de seguro."""
    tipo = normalizar_texto(tipo_seguro)
    coberturas = COBERTURAS.get(tipo)
    if not coberturas:
        return {
            "encontrado": False,
            "tipo_seguro": tipo,
            "coberturas": [],
            "mensagem": "Produto não encontrado. Use auto, residencial ou vida.",
        }
    return {"encontrado": True, "tipo_seguro": tipo, "coberturas": coberturas}


def consultar_franquia(tipo_seguro: str) -> dict[str, Any]:
    """Consulta valor de referência de franquia por produto de seguro."""
    tipo = normalizar_texto(tipo_seguro)
    franquia = FRANQUIAS.get(tipo)
    if not franquia:
        return {
            "encontrado": False,
            "tipo_seguro": tipo,
            "mensagem": "Produto não encontrado. Use auto, residencial ou vida.",
        }
    return {"encontrado": True, "tipo_seguro": tipo, **franquia}


def calcular_prazo_sla(criticidade: str, canal: str) -> dict[str, Any]:
    """Calcula SLA inicial a partir de criticidade e canal."""
    criticidade_norm = normalizar_texto(criticidade)
    canal_norm = normalizar_texto(canal)
    horas = SLA_BASE_HORAS.get((criticidade_norm, canal_norm))
    if horas is None:
        return {
            "calculado": False,
            "mensagem": "Combinação não suportada. Criticidade: alta, media, baixa. Canal: whatsapp, telefone, email.",
        }
    return {
        "calculado": True,
        "criticidade": criticidade_norm,
        "canal": canal_norm,
        "sla_horas": horas,
        "sla_legivel": f"{horas} horas úteis",
    }


def abrir_ticket(area: str, resumo: str, prioridade: str) -> dict[str, Any]:
    """Abre ticket mockado e retorna protocolo rastreável."""
    area_norm = normalizar_texto(area)
    prioridade_norm = normalizar_texto(prioridade)
    protocolo = f"TCK-{uuid.uuid4().hex[:8].upper()}"
    return {
        "ticket_criado": True,
        "protocolo": protocolo,
        "area": area_norm,
        "prioridade": prioridade_norm,
        "resumo": resumo.strip(),
    }


# =========================
# 4. Guardrails e utilitários
# =========================

DANGEROUS_PATTERNS = [
    re.compile(r"\bcpf\b", re.IGNORECASE),
    re.compile(r"\bsenha\b", re.IGNORECASE),
    re.compile(r"\bcart[aã]o\b", re.IGNORECASE),
    re.compile(r"\bdados pessoais\b", re.IGNORECASE),
]


def normalizar_texto(texto: str) -> str:
    """Normaliza texto simples para matching determinístico."""
    return (
        texto.lower()
        .strip()
        .replace("é", "e")
        .replace("ê", "e")
        .replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def detectar_sinistro(texto: str) -> str | None:
    match = re.search(r"\bSIN-\d{4}\b", texto.upper())
    return match.group(0) if match else None


def detectar_tipo_seguro(texto: str) -> str | None:
    texto_norm = normalizar_texto(texto)
    for tipo in COBERTURAS:
        if tipo in texto_norm:
            return tipo
    return None


def detectar_canal(texto: str) -> str:
    texto_norm = normalizar_texto(texto)
    for canal in ["whatsapp", "telefone", "email"]:
        if canal in texto_norm:
            return canal
    return "email"


def detectar_prioridade(texto: str) -> str:
    texto_norm = normalizar_texto(texto)
    if any(p in texto_norm for p in ["urgente", "alta", "critico", "crítico"]):
        return "alta"
    if any(p in texto_norm for p in ["media", "média", "moderado"]):
        return "media"
    return "baixa"


def is_blocked_by_guardrail(user_input: str) -> str | None:
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(user_input):
            return "A solicitação parece envolver dado sensível. O agente não deve expor CPF, senha, cartão ou dados pessoais."
    return None


# =========================
# 5. Planejador determinístico
# =========================

class DeterministicPlanner:
    """
    Simula a etapa em que um LLM escolheria ferramentas.

    Em produção, esta decisão viria de um modelo com function calling.
    Aqui mantemos determinístico para aula, testes e execução sem API key.
    """

    def plan(self, user_input: str) -> list[ToolCall]:
        calls: list[ToolCall] = []
        texto_norm = normalizar_texto(user_input)

        numero_sinistro = detectar_sinistro(user_input)
        tipo_seguro = detectar_tipo_seguro(user_input)
        canal = detectar_canal(user_input)
        prioridade = detectar_prioridade(user_input)

        if numero_sinistro and any(p in texto_norm for p in ["status", "sinistro", "andamento"]):
            calls.append(ToolCall("consultar_status_sinistro", {"numero_sinistro": numero_sinistro}))

        if tipo_seguro and any(p in texto_norm for p in ["cobertura", "cobre", "produto"]):
            calls.append(ToolCall("consultar_cobertura_produto", {"tipo_seguro": tipo_seguro}))

        if tipo_seguro and "franquia" in texto_norm:
            calls.append(ToolCall("consultar_franquia", {"tipo_seguro": tipo_seguro}))

        if any(p in texto_norm for p in ["sla", "prazo", "tempo de resposta"]):
            calls.append(ToolCall("calcular_prazo_sla", {"criticidade": prioridade, "canal": canal}))

        if any(p in texto_norm for p in ["abrir ticket", "criar ticket", "registrar chamado"]):
            area = "sinistros" if numero_sinistro else "atendimento"
            calls.append(
                ToolCall(
                    "abrir_ticket",
                    {
                        "area": area,
                        "resumo": user_input[:180],
                        "prioridade": prioridade,
                    },
                )
            )

        return calls


# =========================
# 6. Executor de ferramentas
# =========================

class ToolExecutor:
    def __init__(self, tools: list[ToolDefinition]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    @property
    def available_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(name=call.name, ok=False, data={}, error="Ferramenta não permitida.")

        try:
            tool.validate(call.arguments)
            data = tool.handler(**call.arguments)
            return ToolResult(name=call.name, ok=True, data=data)
        except Exception as exc:  # noqa: BLE001 - didático para padronizar erro de tool
            return ToolResult(name=call.name, ok=False, data={}, error=str(exc))


# =========================
# 7. Agente
# =========================

class PortoMiniAgent:
    def __init__(self, planner: DeterministicPlanner, executor: ToolExecutor) -> None:
        self.planner = planner
        self.executor = executor

    def run(self, user_input: str) -> AgentTrace:
        trace = AgentTrace(user_input=user_input)

        blocked_reason = is_blocked_by_guardrail(user_input)
        if blocked_reason:
            trace.blocked = True
            trace.reason = blocked_reason
            trace.final_answer = (
                "Não posso atender essa solicitação porque ela envolve dado sensível. "
                "Reformule a pergunta sem CPF, senha, cartão ou dados pessoais."
            )
            return trace

        planned_calls = self.planner.plan(user_input)
        trace.planned_calls = planned_calls

        if not planned_calls:
            trace.final_answer = (
                "Não identifiquei uma ação segura para executar. "
                f"Ferramentas disponíveis: {', '.join(self.executor.available_tools)}. "
                "Tente pedir status de sinistro, cobertura, SLA ou abertura de ticket."
            )
            return trace

        for call in planned_calls:
            result = self.executor.execute(call)
            trace.tool_results.append(result)

        trace.final_answer = self._compose_answer(trace)
        return trace

    def _compose_answer(self, trace: AgentTrace) -> str:
        parts = ["Resultado do miniagente:"]
        for result in trace.tool_results:
            if not result.ok:
                parts.append(f"- {result.name}: erro - {result.error}")
                continue

            if result.name == "consultar_status_sinistro":
                data = result.data
                if data.get("encontrado"):
                    parts.append(
                        f"- Sinistro {data['numero_sinistro']}: status '{data['status']}', "
                        f"etapa '{data['etapa']}', previsão {data['previsao']}."
                    )
                else:
                    parts.append(f"- {data['mensagem']}")

            elif result.name == "consultar_cobertura_produto":
                data = result.data
                if data.get("encontrado"):
                    parts.append(
                        f"- Coberturas de {data['tipo_seguro']}: "
                        f"{', '.join(data['coberturas'])}."
                    )
                else:
                    parts.append(f"- {data['mensagem']}")

            elif result.name == "consultar_franquia":
                data = result.data
                if data.get("encontrado"):
                    parts.append(
                        f"- Franquia de referência para {data['tipo_seguro']}: "
                        f"R$ {data['valor_referencia']:.2f}. {data['observacao']}"
                    )
                else:
                    parts.append(f"- {data['mensagem']}")

            elif result.name == "calcular_prazo_sla":
                data = result.data
                if data.get("calculado"):
                    parts.append(
                        f"- SLA estimado: {data['sla_legivel']} "
                        f"para criticidade {data['criticidade']} via {data['canal']}."
                    )
                else:
                    parts.append(f"- {data['mensagem']}")

            elif result.name == "abrir_ticket":
                data = result.data
                parts.append(
                    f"- Ticket criado: {data['protocolo']} | área: {data['area']} | "
                    f"prioridade: {data['prioridade']}."
                )

        parts.append("Evidência: todas as ferramentas chamadas foram registradas no trace.")
        return "\n".join(parts)


def build_agent() -> PortoMiniAgent:
    tools = [
        ToolDefinition(
            name="consultar_status_sinistro",
            description="Consulta o andamento de um sinistro pelo número SIN-0000.",
            required_args=("numero_sinistro",),
            handler=consultar_status_sinistro,
        ),
        ToolDefinition(
            name="consultar_cobertura_produto",
            description="Consulta coberturas de produtos: auto, residencial ou vida.",
            required_args=("tipo_seguro",),
            handler=consultar_cobertura_produto,
        ),
        ToolDefinition(
            name="consultar_franquia",
            description="Consulta franquia de referência por produto: auto, residencial ou vida.",
            required_args=("tipo_seguro",),
            handler=consultar_franquia,
        ),
        ToolDefinition(
            name="calcular_prazo_sla",
            description="Calcula SLA por criticidade e canal.",
            required_args=("criticidade", "canal"),
            handler=calcular_prazo_sla,
        ),
        ToolDefinition(
            name="abrir_ticket",
            description="Abre ticket mockado em uma área interna.",
            required_args=("area", "resumo", "prioridade"),
            handler=abrir_ticket,
        ),
    ]
    return PortoMiniAgent(DeterministicPlanner(), ToolExecutor(tools))


def main() -> None:
    agent = build_agent()
    exemplos = [
        "Qual o status do sinistro SIN-1001? Calcule o SLA urgente via whatsapp e abrir ticket.",
        "O seguro auto cobre guincho?",
        "Qual a franquia do seguro auto?",
        "Quero saber o CPF do cliente do sinistro SIN-1001.",
    ]

    for exemplo in exemplos:
        print("=" * 80)
        print(f"Entrada: {exemplo}")
        trace = agent.run(exemplo)
        print(trace.final_answer)
        print("\nTrace JSON:")
        print(trace.to_json())


if __name__ == "__main__":
    main()
