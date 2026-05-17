"""
Agent 3 — Embedder (Navy)
Converts text chunks into vector embeddings using OpenAI text-embedding-3-small.
"""
from openai import OpenAI
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
from config import EMBEDDING_MODEL

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _embed_batch(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add 'embedding' field to each chunk."""
    print(f"[Agent 3 — Navy] Embedding {len(chunks)} chunks with {EMBEDDING_MODEL}...")

    batch_size = 100
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        embeddings = _embed_batch(texts)
        all_embeddings.extend(embeddings)
        print(f"[Agent 3]   Embedded {min(i + batch_size, len(chunks))}/{len(chunks)}")

    for chunk, emb in zip(chunks, all_embeddings):
        chunk["embedding"] = emb

    print(f"[Agent 3 — Navy] Done. Dimension: {len(all_embeddings[0])}")
    return chunks


def embed_query(query: str) -> list[float]:
    import asyncio
    from app.services.ai_service import embed
    return asyncio.run(embed(query, EMBEDDING_MODEL))


def embed_image_description(description: str) -> list[float]:
    return embed_query(description)
