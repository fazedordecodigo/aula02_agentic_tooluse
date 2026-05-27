from __future__ import annotations

import re
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CostEstimate:
    monthly_requests: int
    avg_input_tokens: int
    avg_output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    assumptions: list[str]


def _first_int(patterns: list[str], text: str, default: int) -> int:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1).replace(".", "").replace(",", "")
            try:
                return int(raw)
            except ValueError:
                continue
    return default


def estimate_ai_cost_from_text(question: str) -> dict[str, object]:
    """Calculadora real e determinística de custo para exercício FinOps.

    Valores são parâmetros didáticos configuráveis por código. Não dependem de dados
    fictícios de sistemas internos nem simulam resposta de ferramenta externa.
    """
    monthly_requests = _first_int(
        [r"(\d[\d\.,]*)\s*(?:chamadas|requests|requisi[cç][oõ]es)", r"m[eê]s\s*(?:com|de)?\s*(\d[\d\.,]*)"],
        question,
        50_000,
    )
    avg_input_tokens = _first_int(
        [r"(\d[\d\.,]*)\s*tokens?\s*(?:de)?\s*entrada", r"input\s*(?:tokens?)?\s*(\d[\d\.,]*)"],
        question,
        900,
    )
    avg_output_tokens = _first_int(
        [r"(\d[\d\.,]*)\s*tokens?\s*(?:de)?\s*sa[ií]da", r"output\s*(?:tokens?)?\s*(\d[\d\.,]*)"],
        question,
        300,
    )

    # Parâmetros didáticos para comparar cenários. Em produção, substitua por tabela
    # atualizada de preços por modelo/região.
    price_per_1m_input = 0.35
    price_per_1m_output = 1.05
    input_cost = monthly_requests * avg_input_tokens / 1_000_000 * price_per_1m_input
    output_cost = monthly_requests * avg_output_tokens / 1_000_000 * price_per_1m_output

    estimate = CostEstimate(
        monthly_requests=monthly_requests,
        avg_input_tokens=avg_input_tokens,
        avg_output_tokens=avg_output_tokens,
        input_cost_usd=round(input_cost, 4),
        output_cost_usd=round(output_cost, 4),
        total_cost_usd=round(input_cost + output_cost, 4),
        assumptions=[
            "Preço didático: US$ 0.35 por 1M tokens de entrada.",
            "Preço didático: US$ 1.05 por 1M tokens de saída.",
            "Substitua por tabela oficial de pricing no ambiente de produção.",
        ],
    )
    return asdict(estimate)
