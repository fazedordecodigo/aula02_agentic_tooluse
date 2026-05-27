# Arquitetura agentic para AI Experts Porto

Uma arquitetura agentic é uma arquitetura de software na qual um modelo de linguagem participa de decisões controladas. O agente recebe uma intenção, aplica guardrails, escolhe uma rota, chama ferramentas permitidas, observa resultados, verifica completude e responde com evidências.

## Componentes mínimos

- Instruções do sistema: definem papel, limites, linguagem e critérios de segurança.
- Estado: memória operacional do fluxo, contendo pergunta, rota, confiança, risco, contexto recuperado, fontes, resposta e trace.
- Guardrails: bloqueiam pedidos de dados sensíveis, credenciais, prompt injection, vazamento ou bypass de política.
- Roteador: classifica a solicitação em rotas como RAG, FinOps, humano ou bloqueio.
- Ferramentas: capacidades externas permitidas, com contrato claro e validação de argumentos.
- Verificador: avalia se a resposta tem evidência suficiente, se houve erro e se deve escalar.
- Trace: registro auditável das etapas executadas.

## Critério de qualidade

Um agente corporativo confiável não é autonomia sem controle. Ele deve operar com autonomia limitada, rastreabilidade, critérios de aceite, avaliação e fallback humano quando houver baixa confiança ou risco operacional.
