# Exercícios e gabaritos — Aula 6 código real

## Exercício 1 — Adicionar conteúdo à base RAG

### Tarefa

Crie um novo arquivo em `data/knowledge_base/avaliacao_agentes.md` com critérios de avaliação de agentes. Reindexe a base e faça uma pergunta que só possa ser respondida por esse novo arquivo.

### Passos esperados

```bash
cat > data/knowledge_base/avaliacao_agentes.md <<'EOF'
# Avaliação de agentes

Um agente deve ser avaliado por acurácia de rota, groundedness, latência, custo, taxa de fallback humano, taxa de bloqueio correto e satisfação do usuário.
EOF

curl -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{"load_seed": true}'

curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Quais métricas devo usar para avaliar agentes?"}'
```

### Gabarito esperado

A resposta deve citar avaliação por acurácia de rota, groundedness, latência, custo, fallback humano, bloqueio correto e satisfação. O campo `sources` deve incluir `avaliacao_agentes.md`.

---

## Exercício 2 — Adicionar regra de guardrail

### Tarefa

Adicionar bloqueio para solicitações que peçam para apagar base, deletar índice ou dropar tabela.

### Gabarito

Em `app/guardrails.py`, acrescente ao `_BLOCK_PATTERNS`:

```python
(r"apague|delete|deletar|drop table|dropar|remova a base", "Pedido destrutivo não permitido."),
```

Teste unitário sugerido:

```python
def test_guardrail_blocks_destructive_database_request():
    result = check_guardrails("Delete a base vetorial e faça drop table")
    assert not result.allowed
    assert "destrutivo" in result.reason.lower()
```

---

## Exercício 3 — Melhorar fallback por evidência insuficiente

### Tarefa

Modificar `verify_node` para escalar quando a resposta RAG não contiver a seção `Fontes usadas`.

### Gabarito

Em `verify_node`, adicione:

```python
if state.get("route") == "rag" and "fontes usadas" not in answer.lower():
    needs_human = True
```

Critério de aceite: uma resposta gerada sem fontes deve ir para `human_fallback`.

---

## Exercício 4 — Criar tool LangChain adicional

### Tarefa

Criar uma tool `resumir_trace` em `app/tools.py` que receba uma lista de eventos e retorne um resumo dos passos executados.

### Gabarito

```python
@tool
def resumir_trace(eventos: list[dict[str, Any]]) -> str:
    """Resume eventos de trace do agente em uma linha auditável."""
    steps = [str(event.get("step", "unknown")) for event in eventos]
    return "Fluxo executado: " + " > ".join(steps)
```

---

## Exercício 5 — Teste com mock apenas no teste

### Tarefa

Criar uma classe fake para simular resposta de LLM e validar `ai_message_to_text`.

### Gabarito

```python
class FakeAIMessage:
    content = [{"type": "text", "text": "resposta"}]


def test_ai_message_to_text_with_fake_message():
    assert ai_message_to_text(FakeAIMessage()) == "resposta"
```
