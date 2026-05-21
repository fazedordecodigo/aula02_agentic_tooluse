# Aula 01 - Fundamentos de Arquiteturas de Agentes

Kit base para hands-on do Programa AI Experts - Escala (Porto).

Objetivo: mostrar, em codigo simples e evolutivo, a diferenca entre chatbot,
workflow e agente com tool-use, memoria, validacao, logs e fluxo multi-step.

## Estrutura

```text
.
├── pyproject.toml
├── .env.example
├── .agent_memory.example.jsonl
├── data/
│   └── porto_mock_data.json
├── src/
│   └── activities/
│       ├── activity_01_chatbot_vs_workflow_vs_agent.py
│       ├── activity_02_openai_tool_agent.py
│       ├── activity_03_memory_validation_logs.py
│       ├── activity_04_agent_blueprint.py
│       ├── activity_05_langchain_agent_optional.py
│       └── activity_06_pydanticai_agent_optional.py
└── tests/
    └── test_activities.py
```

## Setup

```bash
uv sync --all-extras
cp .env.example .env
```

Para exemplos com OpenAI real:

```bash
export OPENAI_API_KEY="..."
uv run python -m activities.activity_02_openai_tool_agent "Qual o status da apolice 1001?"
```

Sem `OPENAI_API_KEY`, os exemplos rodam em modo deterministico/mocado.

Atalho sem instalar pacote local:

```bash
uv run python -m activities.activity_01_chatbot_vs_workflow_vs_agent
```

## Atividades

### 1. Chatbot vs Workflow vs Agente

Arquivo: `src/activities/activity_01_chatbot_vs_workflow_vs_agent.py`

Mostra 3 abordagens para a mesma pergunta:

- chatbot: resposta textual simples;
- workflow: regra fixa;
- agente: decide qual ferramenta usar.

```bash
uv run python -m activities.activity_01_chatbot_vs_workflow_vs_agent
```

### 2. Miniagente com OpenAI SDK e tool-use

Arquivo: `src/activities/activity_02_openai_tool_agent.py`

Implementa o fluxo oficial de function calling:

1. envia pergunta + definicoes de ferramentas ao modelo;
2. recebe uma ou mais chamadas de ferramenta;
3. executa codigo local;
4. devolve resultado da ferramenta ao modelo;
5. recebe resposta final.

```bash
uv run python -m activities.activity_02_openai_tool_agent "Consolide dados do cliente 42"
```

### 3. Memoria, validacao e logs

Arquivo: `src/activities/activity_03_memory_validation_logs.py`

Evolui o miniagente com:

- memoria curta em arquivo JSONL;
- limite de passos;
- validacao com Pydantic;
- logs estruturados;
- guardrail simples contra operacoes sensiveis.

```bash
uv run python -m activities.activity_03_memory_validation_logs "Resumo do cliente 42"
```

A memoria real fica em `.agent_memory.jsonl`. Esse arquivo e gerado em runtime e
nao e versionado. Use `.agent_memory.example.jsonl` como referencia de formato.

### 4. Blueprint do grupo

Arquivo: `src/activities/activity_04_agent_blueprint.py`

Gera um blueprint inicial do agente para o desafio PBL.

```bash
uv run python -m activities.activity_04_agent_blueprint \
  --problema "analistas consolidam dados manualmente" \
  --objetivo "reduzir tempo de busca interna" \
  --fonte crm --fonte apolices --fonte tickets
```

### 5. Opcional: LangChain

Arquivo: `src/activities/activity_05_langchain_agent_optional.py`

Mostra o padrao moderno `create_agent` com tools Python.

```bash
uv run python -m activities.activity_05_langchain_agent_optional
```

### 6. Opcional: PydanticAI

Arquivo: `src/activities/activity_06_pydanticai_agent_optional.py`

Mostra um agente com dependencia tipada, tool e validacao de saida.

```bash
uv run python -m activities.activity_06_pydanticai_agent_optional
```

## Validacao

```bash
uv run pytest -q
uv run python -m compileall src
```

## Criterios de qualidade usados nos exemplos

- Tool-use explicito e auditavel.
- Dados mockados para evitar dependencia de sistemas reais.
- Limite de passos para reduzir loops.
- Saida validada com schema.
- Logs estruturados por evento.
- Guardrails basicos para acoes sensiveis.
- Fallback deterministico quando nao ha chave de API.

## Fontes consultadas

- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- OpenAI Tools/Responses API: https://platform.openai.com/docs/guides/tools?api-mode=responses
- LangChain Agents: https://docs.langchain.com/oss/python/langchain/agents
- LangChain Tools: https://docs.langchain.com/oss/python/langchain/tools
- PydanticAI Tools/Toolsets: https://ai.pydantic.dev/toolsets/
