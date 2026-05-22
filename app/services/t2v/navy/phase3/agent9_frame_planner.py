"""
Agent 9 — Frame Planner (Navy)
Plans 5-6 keyframe prompts per step, selects reference images.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
from config import LLM_FAST, PLATFORM, IMAGES_DIR
from json_utils import safe_parse_json

SYSTEM_PROMPT = f"""You are a keyframe planner for technical animation videos about the {PLATFORM}.

For each animation step, plan 5 keyframe images. Each keyframe is one still frame in the animation sequence.

For each keyframe provide:
- frame_number: 1-5
- prompt: Detailed image generation prompt. Must specify:
  * "Technical infographic of the LM2500 [specific component]"
  * Clean white/light grey background
  * All parts labeled with callouts
  * Color coding: hot gas=red/orange, compressed air=blue, fuel=green, oil=amber, structure=grey
  * Direction arrows showing flow/rotation
  * Military/naval technical manual aesthetic
  * 1920x1080 resolution
- motion_description: What thermodynamic/mechanical state this frame shows
- sketch_reference: Which reference image to use (filename from available list)

Return JSON:
{{"keyframes": [
  {{"frame_number": 1, "prompt": "...", "motion_description": "...", "sketch_reference": "..."}},
  ...
]}}"""


def plan_frames(step: dict, available_images: list[dict]) -> dict:
    """Plan keyframes for one validated step."""
    image_list = "\n".join([
        f"- {img['filename']}: {img.get('topic', '')} ({img.get('caption', '')[:60]})"
        for img in available_images[:20]
    ])

    import asyncio
    from app.services.ai_service import chat
    resp_text = asyncio.run(chat(
        model=LLM_FAST,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Step {step['step']}: {step['title']}\n"
                f"Description: {step['description']}\n"
                f"Visual focus: {step.get('visual_focus', '')}\n\n"
                f"Available reference images:\n{image_list}"
            )}
        ]
    ))
    
    result = safe_parse_json(resp_text)
    if not result.get("keyframes"):
        import sys
        print(f"[Agent 9 DEBUG] Bad JSON for step {step['step']}:\n{repr(resp_text[:800])}", file=sys.stderr)
    return {
        "step":      step["step"],
        "title":     step["title"],
        "keyframes": result.get("keyframes", []),
    }
