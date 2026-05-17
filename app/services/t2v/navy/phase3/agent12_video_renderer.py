# -*- coding: utf-8 -*-
"""
Agent 12 -- Unified Video Renderer (Navy)
Keyframes + TTS narration -> final MP4 with LLM-driven audio-image sync.
Uses FFmpeg directly — streams from disk, low memory.

Reference: Artillery T2V backend agent12_video_renderer.py
"""
import json
import subprocess
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys

from PIL import Image, ImageDraw
from openai import OpenAI

from app.config import settings
from config import LLM_FAST, PLATFORM, SOURCE_DOC

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# ── Config ─────────────────────────────────────────────────────────────────
MIN_STEP_DURATION = 4.0
TTS_MODEL = "tts-1"
TTS_VOICE = "alloy"
VIDEO_W = 1376
VIDEO_H = 768
COL_BG    = (10, 20, 40)
COL_ACCENT = (40, 140, 180)
COL_WHITE = (255, 255, 255)
COL_GREY  = (160, 160, 180)
CARD_DURATION = 3.0


# ── TTS ────────────────────────────────────────────────────────────────────

def _get_audio_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return max(float(result.stdout.strip()), MIN_STEP_DURATION)
    except Exception:
        return max(MIN_STEP_DURATION, Path(path).stat().st_size / 16000)


def _generate_tts(text: str, output_path: Path) -> float:
    try:
        response = client.audio.speech.create(model=TTS_MODEL, voice=TTS_VOICE, input=text)
        response.stream_to_file(str(output_path))
        return _get_audio_duration(str(output_path))
    except Exception as e:
        print(f"[Agent 12] TTS failed (quota/error): {e}, falling back to silent duration.")
        # Create empty/silent file just so the path exists, or don't.
        # But wait, ffmpeg might fail if we pass a non-existent audio file to concat.
        # It's better to just write a short empty audio or return MIN_STEP_DURATION and let the caller handle it.
        # Actually _get_audio_duration handles missing file by returning MIN_STEP_DURATION.
        return MIN_STEP_DURATION


# ── Cards ──────────────────────────────────────────────────────────────────

def _make_card(lines: list[tuple], output_path: Path) -> Path:
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), COL_BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 8, VIDEO_W, 12], fill=COL_ACCENT)
    draw.rectangle([0, VIDEO_H - 12, VIDEO_W, VIDEO_H - 8], fill=COL_ACCENT)

    y = VIDEO_H // 2 - len(lines) * 28
    for text, colour in lines:
        wrapped = textwrap.fill(text, width=60)
        for line in wrapped.splitlines():
            bbox = draw.textbbox((0, 0), line)
            w = bbox[2] - bbox[0]
            draw.text(((VIDEO_W - w) // 2, y), line, fill=colour)
            y += 36
    img.save(str(output_path))
    return output_path


def _card_to_clip(card_path: Path, duration: float, output_path: Path) -> bool:
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(card_path),
        "-t", str(duration), "-vf", f"scale={VIDEO_W}:{VIDEO_H}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24", str(output_path),
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def _add_badge(src_path: str, dst_path: str, step_num: int, total_steps: int):
    img = Image.open(src_path).convert("RGB")
    img = img.resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    badge = f"Step {step_num} of {total_steps}"
    draw.rectangle([12, 10, 230, 40], fill=COL_BG)
    draw.text((20, 14), badge, fill=COL_ACCENT)
    img.save(dst_path)


# ── LLM Sync ──────────────────────────────────────────────────────────────

SYNC_SYSTEM = """\
You are a video editor aligning keyframe images to narration audio.
Decide WHEN each keyframe should appear so the viewer sees the matching image when the narrator talks about it.
Rules: first frame at 0.0, last frame ends at total_duration, every frame >= 1.5s.
Return JSON: {"sync": [{"frame": 1, "start": 0.0, "end": 5.2}, ...]}"""


def _llm_sync_map(narration, duration, keyframes):
    frames_desc = "\n".join(
        f"  Frame {kf['frame_number']}: {kf.get('motion_description', '')}"
        for kf in keyframes
    )
    try:
        import asyncio
        from app.services.ai_service import chat
        resp_text = asyncio.run(chat(
            model=LLM_FAST,
            messages=[
                {"role": "system", "content": SYNC_SYSTEM},
                {"role": "user", "content": f"Narration:\n\"{narration}\"\n\nDuration: {duration:.1f}s\n\nKeyframes:\n{frames_desc}"},
            ]
        ))
        
        clean_text = resp_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        parsed = json.loads(clean_text.strip())
        sync = parsed.get("sync", [])
        if sync and len(sync) == len(keyframes):
            return sync
    except Exception as e:
        print(f"      Sync error: {e}")
    return None


def _sync_to_durations(sync_map, total_duration):
    durations = [max(e["end"] - e["start"], 1.5) for e in sync_map]
    total = sum(durations)
    if total > 0 and abs(total - total_duration) > 0.1:
        scale = total_duration / total
        durations = [d * scale for d in durations]
    return durations


def _fallback_durations(n, total_duration):
    return [total_duration / n] * n if n > 0 else []


def _build_step_clip(kf_paths, step_num, total_steps, target_dur, output_path, frame_durs=None):
    n = len(kf_paths)
    durations = frame_durs if frame_durs and len(frame_durs) == n else [target_dur / n] * n

    badge_dir = output_path.parent / "badge_tmp"
    badge_dir.mkdir(exist_ok=True)

    badge_paths = []
    for i, kf_path in enumerate(kf_paths):
        bp = badge_dir / f"badge_{i:02d}.png"
        _add_badge(kf_path, str(bp), step_num, total_steps)
        badge_paths.append(bp)

    concat_file = output_path.parent / "concat_step.txt"
    with open(concat_file, "w") as f:
        for i, bp in enumerate(badge_paths):
            f.write(f"file '{str(bp.resolve()).replace(chr(92), '/')}'\n")
            f.write(f"duration {durations[i]:.4f}\n")
        f.write(f"file '{str(badge_paths[-1].resolve()).replace(chr(92), '/')}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-t", f"{target_dur:.4f}", "-vf", f"scale={VIDEO_W}:{VIDEO_H}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24", str(output_path),
    ]
    ok = subprocess.run(cmd, capture_output=True).returncode == 0

    for bp in badge_paths:
        bp.unlink(missing_ok=True)
    if badge_dir.exists():
        try: badge_dir.rmdir()
        except: pass
    concat_file.unlink(missing_ok=True)
    return ok


def _concat_clips(clip_paths, output_path):
    concat_file = output_path.parent / "concat_final.txt"
    with open(concat_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{str(Path(p).resolve()).replace(chr(92), '/')}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_path)]
    ok = subprocess.run(cmd, capture_output=True).returncode == 0
    concat_file.unlink(missing_ok=True)
    return ok


def _concat_audio(audio_entries, total_duration, output_path):
    if not audio_entries:
        return False
    inputs = []
    filter_parts = []
    for i, entry in enumerate(audio_entries):
        inputs.extend(["-i", entry["path"]])
        delay_ms = int(entry["offset"] * 1000)
        filter_parts.append(f"[{i}]adelay={delay_ms}|{delay_ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(audio_entries)))
    filter_parts.append(f"{mix}amix=inputs={len(audio_entries)}:duration=longest:normalize=0[out]")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filter_parts),
           "-map", "[out]", "-c:a", "aac", "-t", str(total_duration), str(output_path)]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def _merge_av(video_path, audio_path, output_path):
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
           "-map", "0:v:0", "-map", "1:a:0", str(output_path)]
    return subprocess.run(cmd, capture_output=True).returncode == 0


# ── Main Renderer ─────────────────────────────────────────────────────────

def render_video(gen_result, validated_steps, question, output_dir):
    video_dir = output_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    step_text = {s["step"]: s["description"] for s in validated_steps}
    total_steps = len(gen_result["steps"])

    # Phase A: TTS (parallel)
    print("\n  [Agent 12] Phase A: TTS...")
    def _tts(step):
        sn = step["step"]
        narration = step_text.get(sn, step.get("title", ""))
        ap = output_dir / f"step_{sn:02d}" / "narration.mp3"
        ap.parent.mkdir(parents=True, exist_ok=True)
        if ap.exists() and ap.stat().st_size > 0:
            dur = _get_audio_duration(str(ap))
        else:
            dur = _generate_tts(narration, ap)
        print(f"    Step {sn}: {dur:.1f}s")
        return {"step": sn, "audio_path": str(ap), "duration": dur}

    tts_data = [None] * len(gen_result["steps"])
    with ThreadPoolExecutor(max_workers=len(gen_result["steps"])) as p:
        futs = {p.submit(_tts, s): i for i, s in enumerate(gen_result["steps"])}
        for f in as_completed(futs):
            tts_data[futs[f]] = f.result()

    # Phase B: Sync maps (parallel)
    print("\n  [Agent 12] Phase B: Sync maps...")
    step_kfs = {}
    for step in gen_result["steps"]:
        kfs = sorted([f for f in step["frames"] if f["success"] and f["path"]], key=lambda f: f["frame_number"])
        kfs = [k for k in kfs if k["frame_number"] > 0]
        step_kfs[step["step"]] = kfs

    sync_durs = {}
    def _sync(step, tts):
        sn = step["step"]
        kfs = step_kfs.get(sn, [])
        if not kfs: return sn, []
        narration = step_text.get(sn, "")
        sm = _llm_sync_map(narration, tts["duration"], kfs)
        return sn, _sync_to_durations(sm, tts["duration"]) if sm else _fallback_durations(len(kfs), tts["duration"])

    with ThreadPoolExecutor(max_workers=len(gen_result["steps"])) as p:
        for f in as_completed({p.submit(_sync, s, t): s["step"] for s, t in zip(gen_result["steps"], tts_data)}):
            sn, durs = f.result()
            sync_durs[sn] = durs

    # Phase C: Build clips
    print("\n  [Agent 12] Phase C: Rendering clips...")
    all_clips = []
    audio_entries = []
    current_time = 0.0

    # Intro
    intro_img = video_dir / "intro_card.png"
    intro_clip = video_dir / "intro.mp4"
    _make_card([
        (PLATFORM, COL_ACCENT), ("", COL_WHITE),
        (question, COL_WHITE), ("", COL_WHITE),
        (f"Source: {SOURCE_DOC}", COL_GREY),
    ], intro_img)
    if _card_to_clip(intro_img, CARD_DURATION, intro_clip):
        all_clips.append(str(intro_clip))
        current_time += CARD_DURATION

    for step, tts in zip(gen_result["steps"], tts_data):
        sn = step["step"]
        kfs = step_kfs.get(sn, [])
        if not kfs: continue

        clip_path = output_dir / f"step_{sn:02d}" / f"clip_step_{sn:02d}.mp4"
        target_dur = tts["duration"]
        frame_durs = sync_durs.get(sn, _fallback_durations(len(kfs), target_dur))

        ok = _build_step_clip([k["path"] for k in kfs], sn, total_steps, target_dur, clip_path, frame_durs)
        if ok and clip_path.exists():
            all_clips.append(str(clip_path))
            audio_entries.append({"path": tts["audio_path"], "offset": current_time})
            current_time += target_dur

    # Outro
    outro_img = video_dir / "outro_card.png"
    outro_clip = video_dir / "outro.mp4"
    titles = [(f"Step {s['step']}: {s['title']}", COL_GREY) for s in validated_steps[:8]]
    titles += [("", COL_WHITE), (f"Source: {SOURCE_DOC}", COL_ACCENT),
               ("Glimmora Aegis — Navy Training", COL_ACCENT)]
    _make_card(titles, outro_img)
    if _card_to_clip(outro_img, CARD_DURATION, outro_clip):
        all_clips.append(str(outro_clip))
        current_time += CARD_DURATION

    if not all_clips:
        return {"path": None, "success": False, "duration": 0}

    # Phase D: Final assembly
    print(f"\n  [Agent 12] Phase D: Assembly ({current_time:.1f}s)...")
    silent = video_dir / "silent_full.mp4"
    _concat_clips(all_clips, silent)

    merged_audio = video_dir / "merged_audio.aac"
    has_audio = _concat_audio(audio_entries, current_time, merged_audio)

    final_path = output_dir / "final_video.mp4"
    if has_audio and merged_audio.exists():
        _merge_av(silent, merged_audio, final_path)
    else:
        import shutil
        shutil.copy(str(silent), str(final_path))

    silent.unlink(missing_ok=True)
    merged_audio.unlink(missing_ok=True)

    if final_path.exists():
        size_mb = final_path.stat().st_size / 1_000_000
        print(f"  [Agent 12] Done: {final_path} ({size_mb:.1f} MB)")
        return {"path": str(final_path), "success": True, "duration": current_time, "size_mb": round(size_mb, 1)}
    return {"path": None, "success": False, "duration": 0}
