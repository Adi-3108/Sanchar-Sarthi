import asyncio

from app.orm.rag_chunk import VECTOR_DIMENSIONS
from app.services.rag_embedding_service import embed_batch, embed_text_sync


def test_fallback_embedding_is_stable_and_expected_dimension():
    first = embed_text_sync("heavy rain waterlogging near silk board junction")
    second = embed_text_sync("heavy rain waterlogging near silk board junction")

    assert len(first) == VECTOR_DIMENSIONS
    assert first == second
    assert any(value != 0 for value in first)


def test_embed_batch_returns_one_embedding_per_input():
    embeddings = asyncio.run(embed_batch(["orr east waterlogging", "mg road vehicle breakdown"]))

    assert len(embeddings) == 2
    assert all(len(embedding) == VECTOR_DIMENSIONS for embedding in embeddings)
