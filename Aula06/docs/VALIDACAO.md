# Validação técnica

## Validações executadas nesta geração

```text
$ python -m compileall app tests scripts
OK

$ python -m pytest -q
..s.........                                                             [100%]
11 passed, 1 skipped in 0.30s
```

## O que foi validado localmente

- Sintaxe de todos os arquivos Python de `app`, `tests` e `scripts`.
- Testes unitários de guardrails, extração de custo, utilitários de texto, helper de chunk id e schema estruturado.
- Teste opcional de runtime LangGraph foi marcado com `pytest.importorskip`, pois as dependências LangChain/LangGraph não estão instaladas neste ambiente local.

## O que requer ambiente real

- Build Docker com instalação das dependências.
- Execução do PostgreSQL/pgvector.
- Chamada real ao Gemini via `GOOGLE_API_KEY` ou `GEMINI_API_KEY`.
- Ingestão real com embeddings Gemini.
- Consulta RAG end-to-end.

## Comandos de validação em ambiente real

```bash
cp .env.example .env
# configure GOOGLE_API_KEY ou GEMINI_API_KEY
docker compose up --build
curl http://localhost:8000/health
curl -X POST http://localhost:8000/ingest -H 'Content-Type: application/json' -d '{"load_seed": true}'
curl -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{"question":"Como funciona RAG com PGVector?"}'
```
