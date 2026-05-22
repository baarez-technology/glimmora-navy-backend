"""
Agent 8 — Validator (Navy)
Cross-checks every step against LM2500 Gas Turbine Course source chunks.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
from config import LLM_FAST, SOURCE_DOC
from json_utils import safe_parse_json

SYSTEM_PROMPT = f"""You are a strict fact-checker for the {SOURCE_DOC}.

You will receive ONE animation step description and source chunks retrieved for this step.

Your job:
1. Read every sentence in the description carefully.
2. Check each factual claim against the provided source chunks.
3. Assign a verdict:
   - VERIFIED:  every claim is supported by the source chunks.
   - CORRECTED: some claims were inaccurate — fix them in validated_description.
   - FLAGGED:   a claim could not be verified at all.
4. The validated_description must still follow the 4-6 sentence educational format.

Return JSON:
{{
  "verdict":               "VERIFIED" | "CORRECTED" | "FLAGGED",
  "confidence":            "HIGH" | "MEDIUM" | "LOW",
  "validated_description": "corrected full description (or unchanged if VERIFIED)",
  "issues":                ["..."] or [],
  "validator_note":        "brief summary"
}}"""


def validate_step(step: dict, evidence_chunks: list[str]) -> dict:
    evidence = "\n\n---\n\n".join(evidence_chunks)
    import asyncio
    from app.services.ai_service import chat
    resp_text = asyncio.run(chat(
        model=LLM_FAST,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Step {step['step']}: {step['title']}\n\n"
                f"Description to validate:\n{step['description']}\n\n"
                f"Source chunks:\n{evidence}"
            )}
        ]
    ))
    return safe_parse_json(resp_text)


def validate_all(steps: list[dict], retriever_fn) -> list[dict]:
    """Validate all steps with fresh per-step evidence."""
    validated = []
    for step in steps:
        evidence = retriever_fn(step["title"], step["description"])
        result = validate_step(step, evidence)

        corrected = result.get("validated_description", "").strip()
        if result.get("verdict") in ("CORRECTED", "FLAGGED") and corrected:
            step["original_description"] = step["description"]
            step["description"] = corrected

        step["validation"] = result
        validated.append(step)
    return validated
