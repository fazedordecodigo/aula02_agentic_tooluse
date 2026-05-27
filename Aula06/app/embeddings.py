from __future__ import annotations

from typing import Iterable

try:
    from langchain_core.embeddings import Embeddings as _Embeddings
except Exception:  # pragma: no cover - permite testes locais sem LangChain instalado
    _Embeddings = object


class GeminiRetrievalEmbeddings(_Embeddings):
    """Adapter de embeddings Gemini para RAG assimétrico.

    Para `gemini-embedding-2`, a documentação do Gemini recomenda prefixar
    consultas e documentos em tarefas de retrieval. Este adapter preserva a
    interface LangChain `Embeddings` usada pelo PGVector e aplica os prefixos.
    """

    def __init__(self, inner: object, document_title: str = "Base de conhecimento Porto AI Experts") -> None:
        self.inner = inner
        self.document_title = document_title

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prepared = [self._prepare_document(text) for text in texts]
        return self.inner.embed_documents(prepared)  # type: ignore[attr-defined]

    def embed_query(self, text: str) -> list[float]:
        return self.inner.embed_query(self._prepare_query(text))  # type: ignore[attr-defined]

    def _prepare_query(self, text: str) -> str:
        return f"task: question answering | query: {text}"

    def _prepare_document(self, text: str) -> str:
        return f"title: {self.document_title} | text: {text}"


def batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]
