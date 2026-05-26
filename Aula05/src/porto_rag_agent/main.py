from __future__ import annotations

import json
from dataclasses import asdict

from .pure_agent import run_agent


def main() -> None:
    examples = [
        ("Qual o status do sinistro SIN-1001? Calcule o SLA urgente via whatsapp e abrir ticket.", "C001"),
        ("O seguro auto cobre guincho?", "C001"),
        ("Qual a franquia do seguro auto?", "C001"),
        ("Suspeita de fraude: login incomum na conta", "C001"),
        ("Quero saber o CPF do cliente do sinistro SIN-1001", "C001"),
    ]
    for message, customer_id in examples:
        state = run_agent(message, customer_id=customer_id)
        print("=" * 88)
        print(f"Entrada: {message}")
        print(state.final_answer)
        print("\nTrace:")
        print(json.dumps(asdict(state), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
