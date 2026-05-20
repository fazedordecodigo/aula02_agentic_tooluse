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

### Executar com Gemini real

Crie um arquivo `.env` local com a chave gerada no Google AI Studio:

```bash
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
```

Depois execute:

```bash
python src/mini_agent_porto.py
```

Quando `GEMINI_API_KEY` existe, o agente usa Gemini automaticamente. Para forçar o modo local, execute com `MINI_AGENT_PLANNER=deterministic`.

## Requisitos

- Python 3.11 ou superior recomendado.
- Não há dependências externas: a chamada ao Gemini usa `urllib` da biblioteca padrão.
- Para usar Gemini real, exige `GEMINI_API_KEY` gerada pelo Google AI Studio.

## O que o miniagente demonstra

- Arquitetura agentic didática.
- Tool registry.
- Tool executor com allowlist.
- Guardrails simples.
- Planner determinístico para simular tool-use.
- Planner Gemini real com function calling.
- Trace JSON para auditoria.
- Testes automatizados.
