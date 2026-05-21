from activities.activity_01_chatbot_vs_workflow_vs_agent import agent_answer
from activities.activity_03_memory_validation_logs import run_guarded_agent
from activities.activity_04_agent_blueprint import create_blueprint


def test_agent_uses_policy_tool() -> None:
    answer = agent_answer("Qual o status da apolice 1001?")
    assert "1001" in answer
    assert "ativa" in answer


def test_guardrail_blocks_sensitive_action() -> None:
    answer = run_guarded_agent("apagar apolice 1001")
    assert answer.status == "blocked"
    assert "acao_sensivel" in answer.risks


def test_blueprint_contains_required_quality_items() -> None:
    blueprint = create_blueprint(
        "busca manual em multiplos sistemas",
        "reduzir tempo de consolidacao",
        ["crm", "apolices"],
    )
    assert "consultar_crm" in blueprint.ferramentas
    assert "validar_consistencia" in blueprint.fluxo
    assert "log_por_tool_call" in blueprint.observabilidade
