from __future__ import annotations

from app.providers import get_runtime_services
from app.rag import index_documents, load_seed_documents


def main() -> None:
    services = get_runtime_services()
    docs = load_seed_documents()
    indexed = index_documents(
        services.vector_store,
        docs,
        chunk_size=services.settings.chunk_size,
        chunk_overlap=services.settings.chunk_overlap,
    )
    print(
        f"Indexed {indexed} chunks from {len(docs)} seed documents "
        f"into collection '{services.settings.vector_collection_name}'."
    )


if __name__ == "__main__":
    main()
