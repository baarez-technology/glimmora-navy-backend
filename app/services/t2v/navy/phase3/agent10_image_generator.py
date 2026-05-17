# -*- coding: utf-8 -*-
"""
Agent 10 -- Image Generator (Navy)
Backend: Gemini 2.5 Flash Image

Bookend+parallel strategy: first/last frames serial for continuity, middle frames parallel.
Reference: Artillery T2V backend agent10_image_generator.py
"""
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
from config import OUTPUT_DIR, PLATFORM

# ── Constants ──────────────────────────────────────────────────────────────
DATA_DIR       = OUTPUT_DIR
GEMINI_MODEL   = "gemini-2.0-flash" 
GEMINI_API_KEY = settings.GOOGLE_API_KEY
MAX_RETRIES    = 3
RETRY_DELAY    = 2
MAX_PARALLEL   = 3
_semaphore     = threading.Semaphore(MAX_PARALLEL)

client = genai.Client(api_key=GEMINI_API_KEY)

STYLE_PREFIX = f"""\
Draw an ORIGINAL technical infographic cutaway diagram for an educational animation.
DO NOT reproduce any existing document, page, or figure. Generate a fresh diagram from scratch.

PLATFORM CONTEXT:
{PLATFORM}

DRAWING STYLE:
- Pure white background, flat engineering cutaway diagram, clean precise lines
- Color coding: moving/active parts orange or red, hydraulic fluid blue, gas pressure yellow, electrical green, fixed structure dark grey
- Bold text labels with thin straight callout lines — ONLY the parts explicitly listed in the prompt
- Direction arrows on every moving part, labeled with the motion direction
- No document headers, page numbers, figure numbers, reference codes, or captions
- 16:9 aspect ratio

DIAGRAM TO DRAW:
"""


def _call_gemini(
    prompt: str,
    ref_image_paths: list[str] | None = None,
    ref_prompt: str | None = None,
) -> Image.Image | None:
    """Gemini image generation — supports reference images for continuity."""
    contents = []

    if ref_image_paths:
        valid = [p for p in ref_image_paths if p and Path(p).exists()]
        if valid:
            for p in valid:
                contents.append(Image.open(p))
            if ref_prompt:
                intro = ref_prompt
            elif len(valid) == 1:
                intro = (
                    "Here is the previous frame of this animation sequence. "
                    "Keep the EXACT same diagram: same camera angle, same art style, "
                    "same colors, same part shapes, same layout. "
                    "Only change what is described below."
                )
            else:
                intro = (
                    "Here are the START frame and END frame of this animation step. "
                    "Keep the EXACT same diagram style. "
                    "Generate the INTERMEDIATE state described below."
                )
            full_prompt = intro + "\n\n" + STYLE_PREFIX + prompt
        else:
            full_prompt = STYLE_PREFIX + prompt
    else:
        full_prompt = STYLE_PREFIX + prompt

    contents.append(full_prompt)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
                image_config=types.ImageConfig(aspect_ratio="16:9"),
            ),
        )
        for part in response.parts:
            if part.inline_data is not None:
                return part.as_image()
        return None
    except Exception as e:
        print(f"      Gemini error: {e}")
        return None


def generate_keyframe(
    keyframe: dict,
    output_path: Path,
    validator_fn=None,
    ref_paths: list[str] | None = None,
    ref_prompt: str | None = None,
) -> dict:
    prompt = keyframe["prompt"]

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"      Frame {keyframe['frame_number']} attempt {attempt}...")
        img = _call_gemini(prompt, ref_image_paths=ref_paths, ref_prompt=ref_prompt)

        if img is None:
            print(f"        FAIL: No image returned")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path))

        if validator_fn is not None:
            val = validator_fn(str(output_path), keyframe["motion_description"])
            if val["verdict"] == "PASS":
                print(f"        OK: Saved + validated")
                return _result(keyframe, output_path, attempt, validated=True)
            else:
                print(f"        FAIL: {val.get('issue', '')}")
                if attempt < MAX_RETRIES:
                    prompt = val.get("refined_prompt", prompt)
                    time.sleep(RETRY_DELAY)
                    continue
                return _result(keyframe, output_path, attempt, validated=False)
        else:
            print(f"        OK: Saved")
            return _result(keyframe, output_path, attempt, validated=None)

    return {
        "frame_number": keyframe["frame_number"],
        "motion_description": keyframe["motion_description"],
        "path": None, "success": False, "attempt": MAX_RETRIES, "validated": False,
    }


def _result(keyframe, path, attempt, validated):
    return {
        "frame_number": keyframe["frame_number"],
        "motion_description": keyframe["motion_description"],
        "path": str(path), "success": True, "attempt": attempt, "validated": validated,
    }


def _generate_with_semaphore(keyframe, output_path, validator_fn, ref_paths, ref_prompt=None):
    with _semaphore:
        return generate_keyframe(keyframe, output_path, validator_fn, ref_paths, ref_prompt)


def _generate_bookends(plan, output_dir, prev_last_frame, validator_fn):
    """Generate first + last frames serial, then middle frames go parallel."""
    import shutil
    step_num = plan["step"]
    step_dir = output_dir / f"step_{step_num:02d}"
    step_dir.mkdir(parents=True, exist_ok=True)
    keyframes = plan["keyframes"]

    continuity = None
    if prev_last_frame and Path(prev_last_frame).exists():
        cont_path = step_dir / "frame_00.png"
        shutil.copy(prev_last_frame, cont_path)
        continuity = {
            "frame_number": 0, "motion_description": "continuity frame",
            "path": str(cont_path), "success": True, "attempt": 0, "validated": True,
        }

    style_ref = [prev_last_frame] if prev_last_frame and Path(prev_last_frame).exists() else None

    first_kf = keyframes[0]
    first_out = step_dir / f"frame_{first_kf['frame_number']:02d}.png"
    print(f"    [bookend A] First frame...")
    first_result = generate_keyframe(first_kf, first_out, validator_fn, ref_paths=style_ref)
    first_result["step"] = step_num
    first_path = first_result["path"] if first_result["success"] else None

    last_result = None
    last_path = None
    if len(keyframes) >= 2:
        last_kf = keyframes[-1]
        last_out = step_dir / f"frame_{last_kf['frame_number']:02d}.png"
        print(f"    [bookend B] Last frame...")
        last_result = generate_keyframe(last_kf, last_out, validator_fn, ref_paths=style_ref)
        last_result["step"] = step_num
        last_path = last_result["path"] if last_result["success"] else None

    return {
        "step_num": step_num, "title": plan["title"], "step_dir": step_dir,
        "keyframes": keyframes, "continuity": continuity,
        "first_result": first_result, "first_path": first_path,
        "last_result": last_result, "last_path": last_path,
        "last_frame_for_chain": last_path or first_path or prev_last_frame,
    }


def generate_all(
    frame_plans: list[dict],
    session_id: str | None = None,
    validator_fn=None,
    _output_dir: Path | None = None,
    _prev_last_frame: str | None = None,
) -> dict:
    if session_id is None:
        session_id = str(int(time.time()))

    output_dir = _output_dir or (DATA_DIR / session_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  [Agent 10] Session: {session_id}, Backend: {GEMINI_MODEL}")

    pool = ThreadPoolExecutor(max_workers=MAX_PARALLEL)
    pending = []
    prev_last_frame = _prev_last_frame

    for plan in frame_plans:
        print(f"\n  [Agent 10] Step {plan['step']}: {plan['title']}")
        bd = _generate_bookends(plan, output_dir, prev_last_frame, validator_fn)
        prev_last_frame = bd["last_frame_for_chain"]

        middle_futures = []
        keyframes = bd["keyframes"]
        if len(keyframes) > 2 and bd["first_path"] and bd["last_path"]:
            middle_kfs = keyframes[1:-1]
            both_refs = [bd["first_path"], bd["last_path"]]
            print(f"    [parallel] {len(middle_kfs)} middle frames...")
            for idx, kf in enumerate(middle_kfs):
                out_path = bd["step_dir"] / f"frame_{kf['frame_number']:02d}.png"
                fut = pool.submit(_generate_with_semaphore, kf, out_path, validator_fn, both_refs)
                middle_futures.append((idx, fut))

        pending.append((bd, middle_futures))

    all_step_results = []
    for bd, middle_futures in pending:
        frame_results = []
        step_num = bd["step_num"]

        if bd["continuity"]:
            frame_results.append(bd["continuity"])
        frame_results.append(bd["first_result"])

        if middle_futures:
            middle_results = [None] * len(middle_futures)
            for idx, fut in middle_futures:
                result = fut.result()
                result["step"] = step_num
                middle_results[idx] = result
            frame_results.extend(middle_results)

        if bd["last_result"]:
            frame_results.append(bd["last_result"])

        success_count = sum(1 for r in frame_results if r and r["success"])
        print(f"    Step {step_num}: {success_count}/{len(frame_results)} frames")

        all_step_results.append({
            "step": step_num, "title": bd["title"],
            "frames": frame_results,
            "last_frame_path": bd["last_frame_for_chain"],
            "success": success_count,
            "failed": len(frame_results) - success_count,
        })

    pool.shutdown(wait=False)

    total = sum(r["success"] + r["failed"] for r in all_step_results)
    success = sum(r["success"] for r in all_step_results)
    print(f"\n  [Agent 10] Done: {success}/{total} frames")

    return {
        "session_id": session_id, "output_dir": str(output_dir),
        "steps": all_step_results, "total": total,
        "success": success, "failed": total - success,
    }
