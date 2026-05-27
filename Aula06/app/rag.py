from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from app.schemas import RawDocument, SourceDocument
from app.text_utils import trim_text


SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"


def load_seed_documents(seed_dir: Path = SEED_DIR) -> list[RawDocument]:
    docs: list[RawDocument] = []
    for path in sorted(seed_dir.glob("*.md")):
        docs.append(
            RawDocument(
                text=path.read_text(encoding="utf-8"),
                source=str(path.relative_to(seed_dir.parent.parent)),
                title=path.stem.replace("_", " ").title(),
                metadata={"kind": "seed", "filename": path.name},
            )
        )
    return docs


def split_documents(raw_docs: list[RawDocument], chunk_size: int, chunk_overlap: int) -> list[object]:
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    base_docs = [
        Document(
            page_content=doc.text,
            metadata={
                "source": doc.source,
                "title": doc.title or doc.source,
                **doc.metadata,
            },
        )
        for doc in raw_docs
    ]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(base_docs)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
        chunk.metadata["chunk_id"] = stable_chunk_id(chunk.page_content, chunk.metadata)
    return chunks


def stable_chunk_id(text: str, metadata: dict[str, Any]) -> str:
    source = str(metadata.get("source", "unknown"))
    title = str(metadata.get("title", "unknown"))
    digest = hashlib.sha256(f"{source}|{title}|{text}".encode("utf-8")).hexdigest()
    return digest[:32]


def index_documents(vector_store: object, raw_docs: list[RawDocument], chunk_size: int, chunk_overlap: int) -> int:
    chunks = split_documents(raw_docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    vector_store.add_documents(chunks, ids=ids)  # type: ignore[attr-defined]
    return len(chunks)


def retrieve_documents(vector_store: object, question: str, top_k: int) -> list[object]:
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})  # type: ignore[attr-defined]
    return list(retriever.invoke(question))


def format_context(docs: list[object], max_chars: int) -> str:
    blocks: list[str] = []
    current_size = 0
    for idx, doc in enumerate(docs, start=1):
        metadata = getattr(doc, "metadata", {}) or {}
        content = getattr(doc, "page_content", "")
        source = metadata.get("source", "desconhecido")
        title = metadata.get("title", source)
        block = f"[Fonte {idx}] title={title} | source={source}\n{content}"
        if current_size + len(block) > max_chars:
            break
        blocks.append(block)
        current_size += len(block)
    return "\n\n".join(blocks)


def to_source_documents(docs: list[object]) -> list[SourceDocument]:
    sources: list[SourceDocument] = []
    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        content = getattr(doc, "page_content", "")
        sources.append(
            SourceDocument(
                source=str(metadata.get("source", "desconhecido")),
                title=metadata.get("title"),
                chunk_id=metadata.get("chunk_id"),
                preview=trim_text(content, max_chars=420),
            )
        )
    return sources
