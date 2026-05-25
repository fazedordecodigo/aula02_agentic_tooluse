"""Deterministic guardrails used before and after the LLM call."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailDecision:
    """Result of a guardrail check."""

    allowed: bool
    code: str
    reason: str


SAFE_BLOCKED_ANSWER = (
    "Não posso seguir com essa solicitação no contexto da demo. "
    "A aula trata de guardrails para agentes de IA; reformule a pergunta "
    "como um pedido de análise, mitigação ou checklist de segurança."
)

TOPIC_KEYWORDS = (
    "guardrail",
    "guardrails",
    "segurança",
    "seguranca",
    "prompt injection",
    "injeção de prompt",
    "injecao de prompt",
    "vazamento",
    "dados sensíveis",
    "dados sensiveis",
    "pii",
    "abuso de ferramenta",
    "tool abuse",
    "allowlist",
    "bloqueio",
    "risco",
    "controle",
    "hardening",
)

INPUT_BLOCK_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(
            r"\b(ignore|desconsidere|bypasse|desative|remova)\b.*"
            r"\b(instru[cç][oõ]es|regras|guardrails?)\b",
            re.IGNORECASE,
        ),
        "prompt_injection",
        "tentativa de contornar instruções ou guardrails",
    ),
    (
        re.compile(
            r"\b(mostre|revele|vaze|exfiltre|imprima)\b.*"
            r"\b(api[_ -]?key|token|senha|segredo|secret)\b",
            re.IGNORECASE,
        ),
        "secret_exfiltration",
        "pedido de exposição de segredo ou credencial",
    ),
    (
        re.compile(
            r"\b(execute|rode|chame)\b.*\b(shell|bash|rm -rf|curl|wget)\b",
            re.IGNORECASE,
        ),
        "unsafe_tool_use",
        "tentativa de executar ação fora da allowlist da demo",
    ),
)

OUTPUT_BLOCK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(api[_ -]?key|token|senha|secret)\b\s*[:=]\s*"
            r"[A-Za-z0-9_\-]{8,}",
            re.IGNORECASE,
        ),
        "possível segredo na resposta",
    ),
    (
        re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
        "possível CPF na resposta",
    ),
    (
        re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "possível número de cartão na resposta",
    ),
)


def check_input(user_input: str) -> GuardrailDecision:
    """Block prompt injection, secret exfiltration and out-of-scope prompts."""
    normalized = user_input.lower()

    for pattern, code, reason in INPUT_BLOCK_PATTERNS:
        if pattern.search(user_input):
            return GuardrailDecision(False, code, reason)

    if not any(keyword in normalized for keyword in TOPIC_KEYWORDS):
        return GuardrailDecision(
            False,
            "out_of_scope",
            "pedido fora do escopo didático de guardrails da aula 4",
        )

    return GuardrailDecision(True, "allowed", "entrada permitida")


def check_output(answer: str) -> GuardrailDecision:
    """Block final answers that appear to expose secrets or personal data."""
    for pattern, reason in OUTPUT_BLOCK_PATTERNS:
        if pattern.search(answer):
            return GuardrailDecision(False, "unsafe_output", reason)

    return GuardrailDecision(True, "allowed", "saída permitida")
