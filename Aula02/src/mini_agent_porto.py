"""
Miniagente corporativo didático para demonstrar Arquitetura Agentic e Tool-Use.

Objetivo pedagógico:
- Mostrar o loop perceber -> planejar -> chamar ferramenta -> observar -> responder.
- Demonstrar allowlist de ferramentas, validação de argumentos, rastreabilidade e guardrails.
- Permitir alternar entre planner determinístico local e planner real via Gemini.

Execução:
    python src/mini_agent_porto.py

Execução com Gemini:
    MINI_AGENT_PLANNER=gemini GEMINI_API_KEY=... python src/mini_agent_porto.py

Testes:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
import json
import os
import re
import urllib.error
import urllib.request
import uuid


GEMINI_ARGUMENT_SCHEMAS = {
    "numero_sinistro": {
        "type": "STRING",
        "description": "Número do sinistro no formato SIN-0000. Exemplo: SIN-1001.",
    },
    "tipo_seguro": {
        "type": "STRING",
        "description": "Tipo de seguro citado pelo usuário.",
        "enum": ["auto", "residencial", "vida"],
    },
    "criticidade": {
        "type": "STRING",
        "description": "Use alta para urgente, crítico ou alta prioridade.",
        "enum": ["alta", "media", "baixa"],
    },
    "canal": {
        "type": "STRING",
        "description": "Canal de atendimento citado pelo usuário. Use email se não houver canal.",
        "enum": ["whatsapp", "telefone", "email"],
    },
    "area": {
        "type": "STRING",
        "description": "Área responsável. Use sinistros quando houver número de sinistro.",
        "enum": ["sinistros", "atendimento"],
    },
    "resumo": {
        "type": "STRING",
        "description": "Resumo curto da solicitação do usuário para abertura do ticket.",
    },
    "prioridade": {
        "type": "STRING",
        "description": "Use alta para urgente, crítico ou alta prioridade.",
        "enum": ["alta", "media", "baixa"],
    },
}


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

    def to_gemini_function_declaration(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    arg: GEMINI_ARGUMENT_SCHEMAS.get(
                        arg,
                        {
                            "type": "STRING",
                            "description": f"Valor obrigatório para o argumento {arg}.",
                        },
                    )
                    for arg in self.required_args
                },
                "required": list(self.required_args),
            },
        }


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
    if criticidade_norm in {"urgente", "critico"}:
        criticidade_norm = "alta"

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


class GeminiPlanner:
    """Planejador real usando Gemini function calling via REST API."""

    def __init__(
        self,
        tools: list[ToolDefinition],
        api_key: str,
        model: str = "gemini-2.5-flash",
        timeout_seconds: int = 30,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")

        self._tools = tools
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def plan(self, user_input: str) -> list[ToolCall]:
        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "Você é o planner de um miniagente corporativo didático. "
                            "Decida quais ferramentas chamar para atender a solicitação. "
                            "Se o usuário pedir múltiplas ações, retorne uma function call "
                            "para cada ação independente. "
                            "Se o usuário pedir abrir, criar ou registrar ticket/chamado, "
                            "inclua a função abrir_ticket. "
                            "Use apenas as funções declaradas. Não invente argumentos. "
                            "Quando uma ferramenta não for necessária, responda sem function call."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_input}],
                }
            ],
            "tools": [
                {
                    "functionDeclarations": [
                        tool.to_gemini_function_declaration() for tool in self._tools
                    ]
                }
            ],
            "toolConfig": {
                "functionCallingConfig": {
                    "mode": "AUTO",
                }
            },
        }

        response = self._post_generate_content(payload)
        return self._extract_tool_calls(response)

    def _post_generate_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Erro HTTP ao chamar Gemini: {exc.code} - {details}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Falha de rede ao chamar Gemini: {exc.reason}") from exc

    def _extract_tool_calls(self, response: dict[str, Any]) -> list[ToolCall]:
        candidates = response.get("candidates", [])
        if not candidates:
            return []

        parts = candidates[0].get("content", {}).get("parts", [])
        calls: list[ToolCall] = []
        for part in parts:
            function_call = part.get("functionCall")
            if not function_call:
                continue

            calls.append(
                ToolCall(
                    name=function_call.get("name", ""),
                    arguments=function_call.get("args", {}),
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
    def __init__(self, planner: Any, executor: ToolExecutor) -> None:
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
            formatted_result = self._format_tool_result(result)
            if formatted_result:
                parts.append(formatted_result)

        parts.append("Evidência: todas as ferramentas chamadas foram registradas no trace.")
        return "\n".join(parts)

    def _format_tool_result(self, result: ToolResult) -> str | None:
        if not result.ok:
            return f"- {result.name}: erro - {result.error}"

        formatters = {
            "consultar_status_sinistro": self._format_status_sinistro,
            "consultar_cobertura_produto": self._format_cobertura_produto,
            "consultar_franquia": self._format_franquia,
            "calcular_prazo_sla": self._format_prazo_sla,
            "abrir_ticket": self._format_ticket,
        }
        formatter = formatters.get(result.name)
        return formatter(result.data) if formatter else None

    def _format_status_sinistro(self, data: dict[str, Any]) -> str:
        if not data.get("encontrado"):
            return f"- {data['mensagem']}"

        return (
            f"- Sinistro {data['numero_sinistro']}: status '{data['status']}', "
            f"etapa '{data['etapa']}', previsão {data['previsao']}."
        )

    def _format_cobertura_produto(self, data: dict[str, Any]) -> str:
        if not data.get("encontrado"):
            return f"- {data['mensagem']}"

        return f"- Coberturas de {data['tipo_seguro']}: {', '.join(data['coberturas'])}."

    def _format_franquia(self, data: dict[str, Any]) -> str:
        if not data.get("encontrado"):
            return f"- {data['mensagem']}"

        return (
            f"- Franquia de referência para {data['tipo_seguro']}: "
            f"R$ {data['valor_referencia']:.2f}. {data['observacao']}"
        )

    def _format_prazo_sla(self, data: dict[str, Any]) -> str:
        if not data.get("calculado"):
            return f"- {data['mensagem']}"

        return (
            f"- SLA estimado: {data['sla_legivel']} "
            f"para criticidade {data['criticidade']} via {data['canal']}."
        )

    def _format_ticket(self, data: dict[str, Any]) -> str:
        return (
            f"- Ticket criado: {data['protocolo']} | área: {data['area']} | "
            f"prioridade: {data['prioridade']}."
        )


def build_tools() -> list[ToolDefinition]:
    return [
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
            description=(
                "Abre ticket mockado em uma área interna. Use quando o usuário pedir "
                "abrir ticket, criar ticket ou registrar chamado."
            ),
            required_args=("area", "resumo", "prioridade"),
            handler=abrir_ticket,
        ),
    ]


def load_env_file(path: str = ".env") -> None:
    """Carrega .env simples sem sobrescrever variáveis já exportadas."""
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def build_agent(planner_mode: str | None = None) -> PortoMiniAgent:
    tools = build_tools()
    default_mode = "gemini" if os.getenv("GEMINI_API_KEY") else "deterministic"
    mode = normalizar_texto(planner_mode or os.getenv("MINI_AGENT_PLANNER", default_mode))

    if mode == "gemini":
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        planner = GeminiPlanner(tools=tools, api_key=os.getenv("GEMINI_API_KEY", ""), model=model)
    elif mode in {"deterministic", "local"}:
        planner = DeterministicPlanner()
    else:
        raise ValueError("MINI_AGENT_PLANNER deve ser 'deterministic' ou 'gemini'.")

    return PortoMiniAgent(planner, ToolExecutor(tools))


def main() -> None:
    load_env_file()
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
