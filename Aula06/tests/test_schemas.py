import pytest
from pydantic import ValidationError

from app.schemas import RouteDecision


def test_route_decision_accepts_valid_structured_output():
    decision = RouteDecision(route="rag", confidence=0.8, risk="baixo", rationale="Pergunta técnica.")
    assert decision.route == "rag"


def test_route_decision_rejects_invalid_route():
    with pytest.raises(ValidationError):
        RouteDecision(route="invalida", confidence=0.8, risk="baixo", rationale="x")
