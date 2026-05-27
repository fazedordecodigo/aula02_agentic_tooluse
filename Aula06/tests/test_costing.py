from app.costing import estimate_ai_cost_from_text


def test_estimate_ai_cost_extracts_values_from_portuguese_text():
    result = estimate_ai_cost_from_text(
        "Estime o custo para 50000 chamadas por mês com 900 tokens de entrada e 300 tokens de saída"
    )
    assert result["monthly_requests"] == 50000
    assert result["avg_input_tokens"] == 900
    assert result["avg_output_tokens"] == 300
    assert result["total_cost_usd"] > 0


def test_estimate_ai_cost_uses_defaults_when_values_missing():
    result = estimate_ai_cost_from_text("Quanto custaria em produção?")
    assert result["monthly_requests"] == 50000
    assert result["avg_input_tokens"] == 900
    assert result["avg_output_tokens"] == 300
