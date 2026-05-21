from __future__ import annotations

import json
import sys
from typing import Any, Callable

from activities.common import configure_environment, get_model_name, has_openai_key, load_mock_data, normalize


def get_weather(city: str) -> str:
    data = load_mock_data()
    return data["clima"].get(normalize(city), f"Sem clima mockado para {city}.")


def get_customer_summary(customer_id: str) -> str:
    data = load_mock_data()
    customer = data["clientes"].get(customer_id)
    if not customer:
        return json.dumps({"erro": "cliente_nao_encontrado", "customer_id": customer_id})
    policies = [data["apolices"][policy_id] for policy_id in customer["apolices"]]
    tickets = [data["tickets"][ticket_id] for ticket_id in customer["tickets"]]
    return json.dumps({"cliente": customer, "apolices": policies, "tickets": tickets}, ensure_ascii=False)


TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Consulta clima mockado por cidade.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "Cidade consultada."}},
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_customer_summary",
        "description": "Consolida dados mockados de cliente, apolices e tickets.",
        "parameters": {
            "type": "object",
            "properties": {"customer_id": {"type": "string", "description": "ID do cliente."}},
            "required": ["customer_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

LOCAL_TOOLS: dict[str, Callable[..., str]] = {
    "get_weather": get_weather,
    "get_customer_summary": get_customer_summary,
}


def call_local_tool(name: str, arguments: dict[str, Any]) -> str:
    tool = LOCAL_TOOLS.get(name)
    if tool is None:
        return json.dumps({"erro": "tool_desconhecida", "tool": name})
    return tool(**arguments)


def run_mock_agent(question: str) -> str:
    text = normalize(question)
    if "clima" in text:
        return f"[mock] {get_weather('Rio de Janeiro')}"
    if "cliente" in text or "42" in text:
        return f"[mock] {get_customer_summary('42')}"
    return "[mock] Nenhuma ferramenta necessaria. Resposta textual simples."


def run_openai_agent(question: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    input_messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "Voce e um miniagente didatico. Use ferramentas quando precisar de dados externos.",
        },
        {"role": "user", "content": question},
    ]

    response = client.responses.create(
        model=get_model_name(),
        input=input_messages,
        tools=TOOLS,
    )

    for item in response.output:
        if item.type != "function_call":
            continue
        result = call_local_tool(item.name, json.loads(item.arguments))
        input_messages.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            }
        )

    if len(input_messages) == 2:
        return response.output_text

    final_response = client.responses.create(
        model=get_model_name(),
        input=input_messages,
        tools=TOOLS,
    )
    return final_response.output_text


def main() -> None:
    configure_environment()
    question = " ".join(sys.argv[1:]) or "Consolide dados do cliente 42"
    answer = run_openai_agent(question) if has_openai_key() else run_mock_agent(question)
    print(answer)


if __name__ == "__main__":
    main()
