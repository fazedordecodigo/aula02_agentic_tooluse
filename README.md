# Aula 2 — Arquitetura Agentic e Tool-Use

Este pacote contém o material da Aula 2 do módulo de Arquiteturas de Agentes e Padrões de Solução.

## Estrutura

```text
aula02_agentic_tooluse/
├── aula_02_arquitetura_agentic_tool_use.md
├── README.md
├── TEST_RESULTS.txt
├── src/
│   ├── __init__.py
│   └── mini_agent_porto.py
└── tests/
    └── test_mini_agent_porto.py
```

## Como executar

```bash
cd aula02_agentic_tooluse
python -m unittest discover -s tests -v
python src/mini_agent_porto.py
```

## Requisitos

- Python 3.11 ou superior recomendado.
- Não há dependências externas.
- Não exige chave de API.

## O que o miniagente demonstra

- Arquitetura agentic didática.
- Tool registry.
- Tool executor com allowlist.
- Guardrails simples.
- Planner determinístico para simular tool-use.
- Trace JSON para auditoria.
- Testes automatizados.
