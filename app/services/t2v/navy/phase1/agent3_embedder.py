"""
Agent 3 — Embedder (Navy)
Converts text chunks into vector embeddings using Google Gemini.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
from config import EMBEDDING_MODEL

_google_client = None


def _get_google_client():
    global _google_client
    if _google_client is None:
        from google import genai
        _google_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    return _google_client


def _embed_single(text: str) -> list[float]:
    client = _get_google_client()
    result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return list(result.embeddings[0].values)


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Google API supports single-item calls,
    so we iterate (but the client is reused)."""
    return [_embed_single(t) for t in texts]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add 'embedding' field to each chunk."""
    print(f"[Agent 3 — Navy] Embedding {len(chunks)} chunks with {EMBEDDING_MODEL}...")

    batch_size = 50
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
    """Embed a query using the same model that indexed ChromaDB (Google Gemini)."""
    return _embed_single(query)


def embed_image_description(description: str) -> list[float]:
    return embed_query(description)
