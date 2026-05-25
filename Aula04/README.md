# Aula 4 — Guardrails e Avaliação Inicial

Projeto didático para workshop de 3h do AI Experts Porto.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Rodar demo completa

```bash
python src/aula04_guardrails_eval_demo.py
```

## Rodar testes

```bash
python -m unittest discover -s tests -v
```

## Rodar boilerplate

```bash
python src/boilerplate_guardrails_langgraph.py
```

## Arquivos

- `src/aula04_guardrails_eval_demo.py`: demo completa com LangChain Tools, LangGraph, guardrails e avaliação inicial.
- `src/boilerplate_guardrails_langgraph.py`: base minimalista para exercícios.
- `tests/test_aula04_guardrails_eval_demo.py`: testes automatizados da demo.
- `AULA_04_GUARDRAILS_E_AVALIACAO_INICIAL.md`: material manuscrito, exercícios, gabaritos e material de apoio.
