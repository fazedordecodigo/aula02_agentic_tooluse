# Aula 5 — RAG aplicado a agentes

Boilerplate e gabarito para laboratório de 3h.

## Rodar o gabarito offline

```bash
cd aula05_rag_aplicado_agentes
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m porto_rag_agent.main
```

## Rodar exemplos LangChain/LangGraph

```bash
pip install -r requirements.txt
PYTHONPATH=src python - <<'PY'
from porto_rag_agent.langchain_rag import build_langchain_vector_store, make_retrieve_context_tool
vs = build_langchain_vector_store()
tool = make_retrieve_context_tool(vs)
print(tool.invoke({"query": "SLA urgente whatsapp"}))
PY
```

```bash
PYTHONPATH=src python - <<'PY'
from porto_rag_agent.langgraph_agent import run_graph
print(run_graph("O seguro auto cobre guincho?", "C001")["final_answer"])
PY
```
