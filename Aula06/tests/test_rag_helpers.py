from app.rag import stable_chunk_id


def test_stable_chunk_id_is_deterministic():
    metadata = {"source": "doc.md", "title": "Doc"}
    first = stable_chunk_id("conteúdo", metadata)
    second = stable_chunk_id("conteúdo", metadata)
    assert first == second
    assert len(first) == 32
