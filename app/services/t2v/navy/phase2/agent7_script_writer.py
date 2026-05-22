"""
Agent 7 — Script Writer (Navy)
Generates animation step scripts from retrieved LM2500 content.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
from config import LLM_STRONG, PLATFORM, SOURCE_DOC
from json_utils import safe_parse_json

SYSTEM_PROMPT = f"""You are a technical animation script writer for the {PLATFORM}.
You generate step-by-step animation scripts from the LM2500 Gas Turbine Course ({SOURCE_DOC}).

Rules:
1. ONLY use content from the provided source chunks. Do NOT add facts not in the source.
2. Generate 5-10 animation steps, each with:
   - step: step number
   - title: concise title (5-10 words)
   - description: 4-6 sentences following this structure:
     Sentence 1: WHAT is happening
     Sentence 2: PART name, what it looks like, where it is
     Sentence 3: HOW it works (mechanical/thermodynamic/hydraulic action)
     Sentence 4: WHY (force, pressure, temperature, design reason)
     Sentence 5+: Result, setup for next step
   - visual_focus: what the animation frame should show
   - source: citation (chapter, page)
3. Every technical term must be defined in plain English in the same sentence.

Return JSON:
{{"steps": [
  {{"step": 1, "title": "...", "description": "...", "visual_focus": "...", "source": "..."}},
  ...
]}}"""


def generate(question: str, chunks: list[dict]) -> list[dict]:
    """Generate animation steps from retrieved chunks."""
    context = "\n\n---\n\n".join([
        f"[Page {c.get('page', '?')} | {c.get('topic', '')}]\n{c['text']}"
        for c in chunks
    ])

    import asyncio
    from app.services.ai_service import chat
    resp_text = asyncio.run(chat(
        model=LLM_STRONG,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Question: {question}\n\n"
                f"Source chunks from {SOURCE_DOC}:\n{context}"
            )}
        ]
    ))

    result = safe_parse_json(resp_text)
    return result.get("steps", [])
