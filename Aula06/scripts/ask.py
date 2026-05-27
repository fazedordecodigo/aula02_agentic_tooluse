from __future__ import annotations

import json
import sys

from app.graph import build_agent_graph
from app.providers import get_runtime_services


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or "Como desenhar guardrails para um agente com RAG?"
    services = get_runtime_services()
    graph = build_agent_graph(services)
    state = graph.invoke({"question": question, "customer_id": "CLI", "trace": []})
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
