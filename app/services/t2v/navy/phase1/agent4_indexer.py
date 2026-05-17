"""
Agent 4 — Indexer (Navy)
Stores all chunks and image metadata in ChromaDB.
"""
import chromadb
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHROMA_DIR, TEXT_COLLECTION, IMAGE_COLLECTION, IMAGES_DIR


def get_client() -> chromadb.PersistentClient:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def index_chunks(chunks: list[dict]) -> None:
    """Store all text chunks with embeddings in ChromaDB."""
    print(f"[Agent 4 — Navy] Indexing {len(chunks)} text chunks...")

    client = get_client()
    collection = client.get_or_create_collection(
        name=TEXT_COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[c["chunk_id"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "page_number": c["page_number"],
                "section":     str(c["section"] or ""),
                "topic":       c["topic"],
                "keywords":    ", ".join(c["keywords"]),
                "figure_refs": ", ".join(c["figure_refs"]),
            } for c in batch],
        )
        print(f"[Agent 4]   Indexed {min(i + batch_size, len(chunks))}/{len(chunks)}")

    print(f"[Agent 4 — Navy] Text collection: {collection.count()} documents")


def index_images(image_records: list[dict]) -> None:
    """Store image metadata in ChromaDB for retrieval during video generation."""
    print(f"[Agent 4 — Navy] Indexing {len(image_records)} images...")

    from agent3_embedder import embed_image_description

    client = get_client()
    collection = client.get_or_create_collection(
        name=IMAGE_COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    for img in image_records:
        description = f"{img['topic']}. {img['caption']}. Page {img['page_number']}."
        emb = embed_image_description(description)

        collection.upsert(
            ids=[img["filename"]],
            embeddings=[emb],
            documents=[description],
            metadatas=[{
                "filename":    img["filename"],
                "file_path":   img["file_path"],
                "page_number": str(img["page_number"]),
                "topic":       img["topic"],
                "caption":     img["caption"],
            }],
        )

    print(f"[Agent 4 — Navy] Image collection: {collection.count()} images")


def verify_retrieval(test_queries: list[str]) -> None:
    """Smoke test retrieval."""
    from agent3_embedder import embed_query

    client = get_client()
    text_col = client.get_collection(TEXT_COLLECTION)
    img_col = client.get_collection(IMAGE_COLLECTION)

    print("\n" + "=" * 60)
    print("RETRIEVAL VERIFICATION — NAVY")
    print("=" * 60)

    for query in test_queries:
        qemb = embed_query(query)
        results = text_col.query(query_embeddings=[qemb], n_results=3)

        print(f"\nQuery: '{query}'")
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            score = round(1 - dist, 3)
            print(f"  [{score}] p{meta['page_number']} | {meta['topic']}")
            print(f"         {doc[:120].encode('ascii', 'replace').decode()}...")

        img_results = img_col.query(query_embeddings=[qemb], n_results=2)
        print("  Images:")
        for meta, dist in zip(img_results["metadatas"][0], img_results["distances"][0]):
            print(f"    [{round(1 - dist, 3)}] {meta['filename']} | {meta['topic']}")
