"""Read-only tools used by the guardrails demo agent."""

from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool

GuardrailPattern = Literal[
    "prompt_injection",
    "data_leakage",
    "tool_abuse",
    "pii",
]

RiskLevel = Literal["baixo", "medio", "alto"]

PATTERNS: dict[str, str] = {
    "prompt_injection": (
        "Prompt injection ocorre quando a entrada tenta alterar instruções, "
        "políticas ou prioridades do agente. Controle mínimo: separar dados "
        "de instruções, usar allowlist de ferramentas e aplicar validação "
        "antes de executar qualquer ação."
    ),
    "data_leakage": (
        "Vazamento de dados ocorre quando a resposta expõe segredos, dados "
        "pessoais ou contexto interno. Controle mínimo: mascaramento, "
        "classificação de dados, menor privilégio e guardrail de saída."
    ),
    "tool_abuse": (
        "Abuso de ferramenta ocorre quando o agente usa uma tool para uma "
        "finalidade não autorizada. Controle mínimo: allowlist, schema rígido, "
        "validação de argumentos, idempotência e auditoria."
    ),
    "pii": (
        "PII inclui dados que podem identificar uma pessoa. Controle mínimo: "
        "não expor, não persistir sem base legal, mascarar nos logs e exigir "
        "autorização explícita por finalidade."
    ),
}

CHECKLISTS: dict[str, list[str]] = {
    "baixo": [
        "Definir escopo do agente.",
        "Registrar trace básico de entrada, rota e resposta.",
        "Usar ferramentas somente leitura.",
    ],
    "medio": [
        "Aplicar guardrail de entrada antes do modelo.",
        "Aplicar allowlist de ferramentas.",
        "Validar argumentos com schema.",
        "Aplicar guardrail de saída antes de responder.",
    ],
    "alto": [
        "Bloquear execução automática de ações sensíveis.",
        "Exigir aprovação humana.",
        "Mascarar dados sensíveis em logs.",
        "Criar teste regressivo para prompt injection e vazamento.",
    ],
}


@tool
def lookup_guardrail_pattern(pattern_type: GuardrailPattern) -> str:
    """Explain one guardrail risk pattern for AI agents.

    Args:
        pattern_type: One of prompt_injection, data_leakage, tool_abuse or pii.
    """
    return PATTERNS[pattern_type]


@tool
def create_guardrail_checklist(risk: RiskLevel) -> str:
    """Create a concise control checklist for a risk level.

    Args:
        risk: Risk level. Use baixo, medio or alto.
    """
    items = CHECKLISTS[risk]
    return "\n".join(f"- {item}" for item in items)


def get_tools() -> list:
    """Return the read-only tools exposed to the LLM."""
    return [lookup_guardrail_pattern, create_guardrail_checklist]
