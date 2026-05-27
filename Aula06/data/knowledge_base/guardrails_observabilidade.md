# Guardrails, segurança e observabilidade

Guardrails devem executar antes de chamadas a ferramentas, retrieval sensível ou ações operacionais. Em um agente de produção, pedidos envolvendo CPF, senha, cartão, API key, token secreto, dados pessoais, exfiltração ou bypass de instruções devem ser bloqueados ou encaminhados para revisão.

## Guardrails mínimos

- Bloquear tentativa de revelar credenciais ou segredos.
- Bloquear solicitação de dados pessoais ou sensíveis.
- Bloquear prompt injection como "ignore as instruções" ou "desative o guardrail".
- Evitar ferramenta sensível antes de validação de risco.
- Registrar motivo do bloqueio em trace técnico.

## Observabilidade mínima

O trace do agente deve registrar: entrada, resultado do guardrail, decisão de rota, confiança, risco, quantidade de documentos recuperados, fontes usadas, geração de resposta, verificação e fallback. O trace não deve expor chain-of-thought privada do modelo.

## Fallback humano

O fallback humano é obrigatório quando a confiança do roteador for baixa, quando não houver evidência recuperada, quando a solicitação for ambígua ou quando houver risco operacional que exceda a autonomia permitida do agente.
