from __future__ import annotations

from activities.common import configure_environment, has_openai_key, load_mock_data


def main() -> None:
    configure_environment()
    if not has_openai_key():
        print("[mock] Instale extras e defina OPENAI_API_KEY para rodar LangChain real.")
        return

    from langchain.agents import create_agent
    from langchain.tools import tool

    @tool
    def get_policy_status(policy_id: str) -> str:
        """Consulta status de uma apolice mockada."""
        policy = load_mock_data()["apolices"].get(policy_id)
        if not policy:
            return "Apolice nao encontrada."
        return f"{policy['produto']} esta {policy['status']}."

    agent = create_agent(
        model="openai:gpt-4.1-mini",
        tools=[get_policy_status],
        system_prompt="Voce e um agente didatico. Use tools para consultar dados.",
    )
    result = agent.invoke({"messages": [{"role": "user", "content": "Status da apolice 1001"}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
