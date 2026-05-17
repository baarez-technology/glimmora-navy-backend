# -*- coding: utf-8 -*-
"""
Phase 3 Orchestrator -- Validated Steps to Video (Navy)
Reference: Artillery T2V backend run_phase3.py
"""
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1"))

from phase3.agent9_frame_planner    import plan_frames
from phase3.agent10_image_generator import generate_all
from phase3.agent11_frame_validator import validate_frame
from phase3.agent12_video_renderer  import render_video
from config import OUTPUT_DIR


def run(
    validated_steps: list[dict],
    question: str,
    session_id: str | None = None,
    use_validator: bool = False,
) -> dict:
    if session_id is None:
        session_id = str(int(time.time()))

    output_dir = OUTPUT_DIR / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    timings = {}
    total_start = time.time()

    # Agent 9: Plan frames
    print(f"\n[Agent 9] Planning keyframes for {len(validated_steps)} steps...")
    t = time.time()
    frame_plans = []
    for step in validated_steps:
        print(f"  Step {step['step']}: {step['title']}")
        plan = plan_frames(step, [])
        frame_plans.append(plan)
    timings["agent9_plan"] = round(time.time() - t, 2)
    total_kf = sum(len(p.get("keyframes", [])) for p in frame_plans)
    print(f"  -> {len(frame_plans)} steps, {total_kf} keyframes planned")

    # Agent 10 + 11: Generate + Validate frames
    validator_fn = validate_frame if use_validator else None
    print(f"\n[Agent 10] Generating images (validator: {use_validator})...")
    t = time.time()
    gen_result = generate_all(frame_plans, session_id, validator_fn=validator_fn, _output_dir=output_dir)
    timings["agent10_generate"] = round(time.time() - t, 2)
    print(f"  -> {gen_result['success']}/{gen_result['total']} frames")

    # Agent 12: Unified render
    print(f"\n[Agent 12] Rendering video (TTS + FFmpeg)...")
    t = time.time()
    video = render_video(gen_result, validated_steps, question, output_dir)
    timings["agent12_render"] = round(time.time() - t, 2)

    timings["total"] = round(time.time() - total_start, 2)

    return {
        "session_id": session_id,
        "output_dir": str(output_dir),
        "video": video,
        "summary": {
            "total_steps": len(validated_steps),
            "total_frames": gen_result["total"],
            "frames_ok": gen_result["success"],
            "video_path": video.get("path"),
            "timings": timings,
        },
    }
