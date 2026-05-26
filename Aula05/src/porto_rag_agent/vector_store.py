from __future__ import annotations

from .models import Document, RetrievedContext
from .text_utils import cosine_similarity, normalize_text


class SimpleVectorStore:
    """Vector store didático sem dependências externas.

    Usa similaridade lexical para permitir validação em qualquer ambiente. Em produção,
    substituir por InMemoryVectorStore, Chroma, PGVector, Qdrant, Pinecone etc.
    """

    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents

    def similarity_search_with_score(self, query: str, k: int = 3, domain: str | None = None) -> list[tuple[Document, float]]:
        candidates = self.documents
        if domain:
            domain_norm = normalize_text(domain)
            candidates = [doc for doc in candidates if normalize_text(str(doc.metadata.get("domain", ""))) == domain_norm]
            if not candidates:
                candidates = self.documents

        scored = [(doc, cosine_similarity(query, doc.page_content)) for doc in candidates]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:k]

    def retrieve(self, query: str, k: int = 3, domain: str | None = None, min_score: float = 0.05) -> RetrievedContext:
        scored = self.similarity_search_with_score(query=query, k=k, domain=domain)
        filtered = [(doc, score) for doc, score in scored if score >= min_score]
        documents = [doc for doc, _ in filtered]
        scores = [score for _, score in filtered]
        serialized = "\n\n".join(
            f"<doc source_id=\"{doc.metadata.get('source_id')}\" title=\"{doc.metadata.get('title')}\">\n"
            f"{doc.page_content}\n</doc>"
            for doc in documents
        )
        return RetrievedContext(query=query, documents=documents, serialized_context=serialized, scores=scores)
