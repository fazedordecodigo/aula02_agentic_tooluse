# FinOps de IA para agentes

FinOps de IA trata o consumo de modelos como uma disciplina de engenharia e produto. O custo de um agente depende do número de chamadas, tokens de entrada, tokens de saída, modelo usado, retries, retrieval, observabilidade, cache e latência esperada.

## Controles recomendados

- Medir custo por rota: RAG, FinOps, humano e bloqueio.
- Registrar tokens de entrada, saída e total quando o provedor retornar metadados.
- Aplicar cache para perguntas repetidas e documentos frequentes.
- Reduzir contexto com chunking adequado e `top_k` controlado.
- Usar modelos menores ou mais baratos para roteamento quando a tarefa permitir.
- Definir orçamento, alertas e limites por ambiente.

## Estimativa de custo

Uma estimativa didática pode usar: chamadas por mês, tokens médios de entrada, tokens médios de saída, preço por 1 milhão de tokens de entrada e preço por 1 milhão de tokens de saída. A fórmula é: chamadas × tokens / 1.000.000 × preço.
