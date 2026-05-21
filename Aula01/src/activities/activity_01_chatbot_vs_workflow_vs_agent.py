from __future__ import annotations

from activities.common import load_mock_data, normalize


def chatbot_answer(question: str) -> str:
    return f"Recebi sua pergunta: {question}. Posso ajudar com informações gerais."


def workflow_answer(question: str) -> str:
    if "apólice" in normalize(question):
        return "Workflow fixo: consulte o sistema de apólices."
    return "Workflow fixo: abra um chamado para classificação manual."


def search_policy(policy_id: str) -> str:
    data = load_mock_data()
    policy = data["apolices"].get(policy_id)
    if not policy:
        return f"Apólice {policy_id} nao encontrada."
    return f"Apólice {policy_id}: {policy['produto']} está {policy['status']}."


def agent_answer(question: str) -> str:
    text = normalize(question)
    if "1001" in text:
        return search_policy("1001")
    if "1002" in text:
        return search_policy("1002")
    return "Agente: preciso escolher outra ferramenta ou pedir mais contexto."


def main() -> None:
    question = "Qual o status da apólice 1001?"
    print("Pergunta:", question)
    print("Chatbot:", chatbot_answer(question))
    print("Workflow:", workflow_answer(question))
    print("Agente:", agent_answer(question))


if __name__ == "__main__":
    main()
