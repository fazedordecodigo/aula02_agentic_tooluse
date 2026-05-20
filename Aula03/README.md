# Aula 3 — Arquitetura de Agentes: Multi-step Reasoning e Roteamento

Este projeto apresenta uma implementação didática e sem dependências externas de uma **Arquitetura de Agente Baseada em Estado (State-based Agent)**. O sistema utiliza uma esteira linear (pipeline) de etapas funcionais para ler, transformar e responder a solicitações de clientes de forma segura e transparente.

---

## 📌 Fluxo Geral do Código (Flowchart)

O fluxograma abaixo detalha como o estado da conversa (`AgentState`) trafega sequencialmente por cada etapa do pipeline, desde o recebimento da mensagem do usuário até a formatação da resposta em linguagem natural.

```mermaid
flowchart TD
    Start([Início: run_agent]) --> InitState[Inicializa AgentState]
    InitState --> Step1[1. Roteamento: route_message]
    
    Step1 --> CalcScore[Calcula pontuação de palavras-chave]
    CalcScore --> CheckConf{Confiança < 0.35?}
    CheckConf -- Sim --> RouteHuman[Define rota = HUMANO]
    CheckConf -- Não --> RouteHigh[Define rota = Maior Score]
    
    RouteHuman --> Step2[2. Planejamento: build_plan]
    RouteHigh --> Step2
    
    Step2 --> GetPlan[Busca lista de tarefas pré-definidas]
    GetPlan --> Step3[3. Execução: execute_tools]
    
    Step3 --> Guardrail[s19]
    Guardrail -- Sim --> BlockRoute[Define rota = BLOQUEADO]
    Guardrail -- Não --> ExecDispatch[Executa ferramenta via Dispatch Map]
    
    BlockRoute --> Step4[4. Verificação: verify_results]
    ExecDispatch --> Step4
    
    Step4 --> CheckBlocked[s20]
    CheckBlocked -- Sim --> Step5[5. Resposta: compose_answer]
    CheckBlocked -- Não --> CheckFailures[s21]
    
    CheckFailures -- Sim --> RouteHumanFallback[Define rota = HUMANO & Abre ticket]
    CheckFailures -- Não --> Step5
    
    RouteHumanFallback --> Step5
    
    Step5 --> FormatDispatch[s22]
    FormatDispatch -- Sim --> FormatLambda[Formata resposta usando Lambda/Função mapeada]
    FormatDispatch -- Não --> FormatKB["Formata resposta da Roteamento Geral (KB)"]
    
    FormatLambda --> End([Fim: Retorna AgentState])
    FormatKB --> End
```

---

## 🔄 Diagrama de Sequência

Este diagrama ilustra a interação temporal e a troca de dados entre o Orquestrador do Agente, o objeto de Estado compartilhado, as etapas de execução e as APIs/Ferramentas externas mockadas.

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuário / Cliente
    participant Agent as Agent (run_agent)
    participant State as Estado (AgentState)
    participant Steps as Pipeline Steps (Router/Planner/Verifier/Composer)
    participant Tools as Ferramentas (Guardrails/CRM/KB)

    User->>Agent: Envia mensagem e customer_id
    activate Agent
    
    Agent->>State: Cria instância com mensagem e customer_id
    activate State
    State-->>Agent: Estado inicializado
    deactivate State
    
    %% 1. Routing
    Agent->>Steps: route_message(state)
    activate Steps
    Steps->>State: Lê user_message
    Steps->>State: Escreve route, confidence, rationale, trace
    Steps-->>Agent: Retorna estado atualizado
    deactivate Steps
    
    %% 2. Planning
    Agent->>Steps: build_plan(state)
    activate Steps
    Steps->>State: Lê route
    Steps->>State: Escreve plan, trace
    Steps-->>Agent: Retorna estado atualizado
    deactivate Steps
    
    %% 3. Executing Tools (with Guardrail)
    Agent->>Steps: execute_tools(state)
    activate Steps
    
    Steps->>Tools: detect_policy_violation(user_message)
    activate Tools
    Tools-->>Steps: Retorna ToolResult (Guardrail)
    deactivate Tools
    Steps->>State: Registra ToolResult
    
    alt Guardrail Violated
        Steps->>State: Escreve route = BLOQUEADO
    else Guardrail OK
        Steps->>Tools: Invoca ferramenta de negócio via Dispatch Map
        activate Tools
        Tools-->>Steps: Retorna ToolResult
        deactivate Tools
        Steps->>State: Registra ToolResult
    end
    Steps-->>Agent: Retorna estado atualizado
    deactivate Steps
    
    %% 4. Verification
    Agent->>Steps: verify_results(state)
    activate Steps
    Steps->>State: Lê tool_results
    alt Tool Failure Detected
        Steps->>State: Escreve route = HUMANO
        Steps->>Tools: open_human_ticket(...)
        activate Tools
        Tools-->>Steps: Retorna ToolResult (Ticket)
        deactivate Tools
        Steps->>State: Registra ToolResult (Ticket)
    end
    Steps-->>Agent: Retorna estado atualizado
    deactivate Steps
    
    %% 5. Compose Answer
    Agent->>Steps: compose_answer(state)
    activate Steps
    Steps->>State: Lê route e tool_results
    Steps->>State: Escreve final_answer
    Steps-->>Agent: Retorna estado atualizado
    deactivate Steps
    
    Agent->>User: Exibe a resposta final do Estado (final_answer)
    deactivate Agent
```

---

## 🛠️ Padrões de Projeto Utilizados

A arquitetura deste agente foi estruturada seguindo práticas sólidas de engenharia de software para garantir que o código seja limpo, modular e fácil de manter:

1. **State-Based Agent (Padrão de Estado)**: Todas as decisões e históricos de execuções são mantidos na classe de dados `AgentState`. Isso garante rastreabilidade total (`trace`) e evita que as funções do pipeline gerem efeitos colaterais incontroláveis.
2. **Linear Pipeline / Pipe & Filter**: A orquestração do ciclo de vida é composta por uma lista sequencial de chamadas (`STEPS`), o que simplifica o fluxo de execução e a escrita de testes unitários determinísticos.
3. **Dispatch Map (Tabela de Roteamento/Despacho)**: Em vez de cadeias aninhadas de `if/elif/else` na execução de ferramentas e formatação de respostas, o código utiliza dicionários associando instâncias de rotas a comportamentos específicos (lambdas e funções locais). Isso torna a expansão do agente extremamente modular.
4. **Input Guardrail Pattern**: Interceptação e sanitização de solicitações na primeira barreira física antes de rodar qualquer código crítico de CRM, garantindo robustez de segurança.
