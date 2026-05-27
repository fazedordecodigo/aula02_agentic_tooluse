# RAG com embeddings e banco vetorial

RAG, ou Retrieval-Augmented Generation, combina recuperação de informação com geração de texto. O fluxo recomendado para o laboratório é: preparar documentos, quebrar em chunks, gerar embeddings, armazenar os vetores em banco vetorial, recuperar os trechos mais relevantes para uma pergunta e então pedir ao LLM que responda usando apenas esse contexto.

## Pipeline de ingestão

1. Carregar documentos de conhecimento.
2. Dividir os documentos em chunks com sobreposição.
3. Gerar embeddings para cada chunk.
4. Persistir os chunks e seus metadados em PostgreSQL com extensão pgvector.
5. Usar IDs determinísticos para evitar duplicidade na reingestão.

## Pipeline de consulta

1. Receber a pergunta.
2. Gerar embedding da pergunta.
3. Buscar os chunks mais similares no PGVector.
4. Montar contexto com fonte, título e conteúdo.
5. Gerar resposta com Gemini usando o contexto recuperado.
6. Retornar resposta, fontes e trace.

## Boas práticas

- Use metadados de fonte e título em todos os chunks.
- Defina `top_k` conforme qualidade e latência.
- Evite responder sem contexto recuperado.
- Faça avaliação com perguntas esperadas, perguntas fora do escopo e tentativas de prompt injection.
