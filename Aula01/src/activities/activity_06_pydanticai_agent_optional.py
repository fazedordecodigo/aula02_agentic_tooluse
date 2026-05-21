from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass

from activities.common import configure_environment, has_openai_key, load_mock_data


@dataclass
class PortoDeps:
    data: dict


@dataclass
class MockPolicyAnswer:
    policy_id: str
    status: str
    recommendation: str


def main() -> None:
    configure_environment()
    if not has_openai_key():
        print("[mock] PydanticAI real exige OPENAI_API_KEY. Saida validada localmente:")
        answer = MockPolicyAnswer(policy_id="1001", status="ativa", recommendation="manter acompanhamento")
        print(json.dumps(asdict(answer), ensure_ascii=False))
        return

    from pydantic_ai import Agent, RunContext
    from pydantic import BaseModel

    class PolicyAnswer(BaseModel):
        policy_id: str
        status: str
        recommendation: str

    agent = Agent(
        "openai:gpt-4.1-mini",
        deps_type=PortoDeps,
        output_type=PolicyAnswer,
        system_prompt="Voce consulta apolices mockadas e responde no schema definido.",
    )

    @agent.tool
    def get_policy_status(ctx: RunContext[PortoDeps], policy_id: str) -> str:
        """Consulta uma apolice mockada."""
        policy = ctx.deps.data["apolices"].get(policy_id)
        if not policy:
            return "nao_encontrada"
        return policy["status"]

    result = agent.run_sync(
        "Qual o status da apolice 1001 e a recomendacao?",
        deps=PortoDeps(data=load_mock_data()),
    )
    print(result.output.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
