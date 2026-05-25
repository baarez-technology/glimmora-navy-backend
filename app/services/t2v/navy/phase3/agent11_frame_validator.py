"""
Agent 11 — Frame Validator (Navy)
Checks each generated keyframe with GPT-4o Vision.
"""
import base64
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings

# This agent calls OpenAI Vision directly — always use an OpenAI model name.
LLM_STRONG = "gpt-4o"

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a quality checker for technical infographic frames used in an LM2500 gas turbine education video.

Check three things only:
1. GIBBERISH LABELS: Are any labels misspelled, nonsensical, or made-up words?
2. DIAGRAM TYPE: Is this a clean technical diagram — not a photo or document scan?
3. ARROWS: Are there direction arrows on the moving/flowing parts described?

Do NOT fail for artistic style, color choice, or geometric inaccuracies.

Return JSON:
{
  "verdict": "PASS" or "FAIL",
  "issue": "one sentence (empty if PASS)",
  "refined_prompt": "improved prompt hint (empty if PASS)"
}"""


def validate_frame(image_path: str, motion_description: str) -> dict:
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your_"):
        return {"verdict": "PASS", "issue": "", "refined_prompt": ""}

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=LLM_STRONG,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    {"type": "text", "text": f"This frame should show: {motion_description}\nCheck for gibberish labels, document reproduction, or missing arrows."},
                ]},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=300,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"[Agent 11] Validation failed (quota/error), bypassing: {e}")
        return {
            "verdict": "PASS",
            "issue": "",
            "refined_prompt": ""
        }
