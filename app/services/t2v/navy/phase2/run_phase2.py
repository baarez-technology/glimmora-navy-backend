"""
Phase 2 Orchestrator — Navy (LM2500 Gas Turbine)
Question -> Validated Animation Steps

Usage:
    cd t2v/navy/phase2
    python run_phase2.py "How does the LM2500 compressor work?"
"""
import time
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1"))

from agent5_question_analyzer import analyze
from agent6_rag_retriever      import retrieve, retrieve_for_step
from agent7_script_writer      import generate
from agent8_validator           import validate_all
from config                     import PLATFORM


def run(question: str) -> dict:
    print("=" * 60)
    print(f"PHASE 2 — NAVY: {question}")
    print("=" * 60)

    total_start = time.time()
    timings = {}

    # Agent 5
    print("\n[Agent 5] Analyzing question...")
    t = time.time()
    intent = analyze(question)
    timings["agent5_analyze"] = time.time() - t
    print(f"  Topic: {intent['primary_topic']}")
    print(f"  Type:  {intent['question_type']}")

    # Agent 6
    print("\n[Agent 6] Retrieving from knowledge base...")
    t = time.time()
    results = retrieve(intent)
    timings["agent6_retrieve"] = time.time() - t
    print(f"  Chunks: {len(results['chunks'])}")
    print(f"  Images: {len(results['images'])}")

    # Agent 7
    print("\n[Agent 7] Generating animation steps...")
    t = time.time()
    steps = generate(question, results["chunks"])
    timings["agent7_generate"] = time.time() - t
    print(f"  Steps generated: {len(steps)}")

    # Agent 8
    print("\n[Agent 8] Validating each step...")
    t = time.time()
    validated_steps = validate_all(steps, retrieve_for_step)
    timings["agent8_validate"] = time.time() - t

    verdicts = [s["validation"]["verdict"] for s in validated_steps]
    timings["total"] = time.time() - total_start

    summary = {
        "total_steps": len(validated_steps),
        "verified":    verdicts.count("VERIFIED"),
        "corrected":   verdicts.count("CORRECTED"),
        "flagged":     verdicts.count("FLAGGED"),
        "timings":     timings,
    }

    print(f"\n{'=' * 60}")
    print(f"PHASE 2 COMPLETE — {PLATFORM}")
    print(f"Steps: {summary['total_steps']} | "
          f"Verified: {summary['verified']} | "
          f"Corrected: {summary['corrected']} | "
          f"Flagged: {summary['flagged']}")
    print(f"Total time: {timings['total']:.1f}s")
    print(f"{'=' * 60}")

    return {
        "question":        question,
        "intent":          intent,
        "retrieved_images": results["images"],
        "steps":           validated_steps,
        "summary":         summary,
    }


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "How does the LM2500 compressor work?"
    result = run(q)
    print(json.dumps(result["summary"], indent=2))
