from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str | None = None
    matched_pattern: str | None = None


_BLOCK_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"ignore (as )?instru[cç][oõ]es", "Tentativa de ignorar instruções do sistema."),
    (r"desative|burlar|bypass|jailbreak", "Tentativa de burlar controles do agente."),
    (r"api[_\s-]?key|chave secreta|segredo|token secreto", "Pedido de segredo ou credencial."),
    (r"\bsenha\b|password", "Pedido de senha ou credencial."),
    (r"\bcpf\b|\brg\b|cart[aã]o|dados pessoais", "Pedido envolvendo dado pessoal ou sensível."),
    (r"exfiltre|vaze|roube|dump", "Pedido de exfiltração ou vazamento de dados."),
)


def check_guardrails(user_input: str) -> GuardrailResult:
    normalized = user_input.strip().lower()
    for pattern, reason in _BLOCK_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return GuardrailResult(allowed=False, reason=reason, matched_pattern=pattern)
    return GuardrailResult(allowed=True)
