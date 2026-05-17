"""
Phase 1 Orchestrator — Navy (LM2500 Gas Turbine)
Runs all 4 agents to build the knowledge base.

Usage:
    cd t2v/navy/phase1
    python run_phase1.py
"""
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent1_pdf_parser import parse_pdf, extract_images
from agent2_chunker    import chunk_pages
from agent3_embedder   import embed_chunks
from agent4_indexer    import index_chunks, index_images, verify_retrieval
from config            import PDF_PATH, CHROMA_DIR, PLATFORM, SOURCE_DOC


def run():
    print("=" * 60)
    print("PHASE 1 — NAVY DOCUMENT GROUNDING")
    print(f"Platform: {PLATFORM}")
    print(f"Source: {SOURCE_DOC}")
    print("=" * 60)

    if not PDF_PATH.exists():
        print(f"ERROR: PDF not found at {PDF_PATH}")
        return

    total_start = time.time()

    # Agent 1: Parse PDF
    print("\n[STEP 1/5] Agent 1 — PDF Parser")
    t = time.time()
    pages = parse_pdf()
    print(f"           Done in {time.time() - t:.1f}s | Pages: {len(pages)}")

    # Agent 1b: Extract images
    print("\n[STEP 2/5] Agent 1 — Image Extractor")
    t = time.time()
    image_records = extract_images()
    print(f"           Done in {time.time() - t:.1f}s | Images: {len(image_records)}")

    # Agent 2: Chunk
    print("\n[STEP 3/5] Agent 2 — Chunker")
    t = time.time()
    chunks = chunk_pages(pages)
    print(f"           Done in {time.time() - t:.1f}s | Chunks: {len(chunks)}")

    # Agent 3: Embed
    print("\n[STEP 4/5] Agent 3 — Embedder")
    t = time.time()
    chunks = embed_chunks(chunks)
    print(f"           Done in {time.time() - t:.1f}s | Dim: {len(chunks[0]['embedding'])}")

    # Agent 4: Index
    print("\n[STEP 5/5] Agent 4 — Indexer")
    t = time.time()
    index_chunks(chunks)
    index_images(image_records)
    print(f"           Done in {time.time() - t:.1f}s")
    print(f"           ChromaDB: {CHROMA_DIR}")

    total = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"PHASE 1 NAVY COMPLETE in {total:.1f}s")
    print(f"{'=' * 60}")

    # Smoke test
    verify_retrieval([
        "How does the LM2500 compressor work?",
        "How does the combustion section ignite fuel?",
        "What is the lube oil system?",
        "How does the hydraulic start system work?",
        "What is the firing sequence?",
    ])

    return {"chunks": len(chunks), "images": len(image_records), "time": total}


if __name__ == "__main__":
    run()
