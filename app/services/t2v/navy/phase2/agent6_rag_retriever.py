"""
Agent 6 — RAG Retriever (Navy)
Retrieves relevant text chunks and images from ChromaDB.
"""
import chromadb
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1"))
from config import CHROMA_DIR, TEXT_COLLECTION, IMAGE_COLLECTION
from agent3_embedder import embed_query

_client = None
_text_collection = None
_img_collection = None


def _get_collections():
    global _client, _text_collection, _img_collection
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _text_collection = _client.get_collection(TEXT_COLLECTION)
        _img_collection = _client.get_collection(IMAGE_COLLECTION)
    return _text_collection, _img_collection


def retrieve(intent: dict, top_k: int = 8) -> dict:
    """Retrieve relevant chunks and images for an intent."""
    text_col, img_col = _get_collections()
    query_str = intent["original_question"] + " " + " ".join(intent.get("search_terms", []))
    query_emb = embed_query(query_str)

    text_results = text_col.query(query_embeddings=[query_emb], n_results=top_k)
    img_results = img_col.query(query_embeddings=[query_emb], n_results=4)

    chunks = []
    for doc, meta, dist in zip(
        text_results["documents"][0], text_results["metadatas"][0], text_results["distances"][0]
    ):
        chunks.append({
            "text": doc, "score": round(1 - dist, 3),
            "page": meta.get("page_number"), "section": meta.get("section"),
            "topic": meta.get("topic"), "figure_refs": meta.get("figure_refs", ""),
        })

    images = []
    for meta, dist in zip(img_results["metadatas"][0], img_results["distances"][0]):
        images.append({
            "filename": meta.get("filename"), "file_path": meta.get("file_path"),
            "topic": meta.get("topic"), "score": round(1 - dist, 3),
        })

    return {"query_used": query_str, "query_emb": query_emb, "chunks": chunks, "images": images}


def retrieve_for_step(step_title: str, step_description: str, top_k: int = 4) -> list[str]:
    """Retrieve chunks for one step — used by Validator (Agent 8)."""
    text_col, _ = _get_collections()
    query_str = step_title + " " + step_description[:200]
    query_emb = embed_query(query_str)
    results = text_col.query(query_embeddings=[query_emb], n_results=top_k)
    return results["documents"][0]
