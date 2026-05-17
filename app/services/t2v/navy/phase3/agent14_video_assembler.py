"""
Agent 14 — Video Assembler (Navy)
Stitches all step clips into the final video with intro/outro and overlays.
"""
import subprocess
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PLATFORM, SOURCE_DOC

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def assemble_video(
    clip_paths: list[str],
    question: str,
    step_titles: list[str],
    output_path: str,
    fps: int = 24,
) -> dict:
    """Stitch all step clips + intro/outro into final MP4."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    all_inputs = []

    intro_path = str(Path(output_path).parent / "intro_card.mp4")
    if PIL_AVAILABLE:
        _create_card_video(
            text_lines=[PLATFORM, "", question, "", f"Source: {SOURCE_DOC}"],
            output_path=intro_path,
            duration=3, fps=fps,
            bg_color=(10, 30, 60), text_color="white",
        )
        if Path(intro_path).exists():
            all_inputs.append(intro_path)

    for p in clip_paths:
        if p and Path(p).exists():
            all_inputs.append(p)

    outro_path = str(Path(output_path).parent / "outro_card.mp4")
    if PIL_AVAILABLE:
        steps_text = "\n".join([f"  {i+1}. {t}" for i, t in enumerate(step_titles)])
        _create_card_video(
            text_lines=[
                "Steps Covered:", "", steps_text, "",
                f"Source: {SOURCE_DOC}",
                "Glimmora Aegis — Navy Training Platform",
            ],
            output_path=outro_path,
            duration=3, fps=fps,
            bg_color=(10, 30, 60), text_color="white",
        )
        if Path(outro_path).exists():
            all_inputs.append(outro_path)

    if not all_inputs:
        return {"video_path": None, "error": "No clips to assemble"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in all_inputs:
            f.write(f"file '{p.replace(chr(92), '/')}'\n")
        concat_file = f.name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-r", str(fps), output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=300)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"video_path": None, "error": str(e)}

    Path(concat_file).unlink(missing_ok=True)
    return {"video_path": output_path if Path(output_path).exists() else None, "total_clips": len(clip_paths)}


def _create_card_video(text_lines, output_path, duration=3, fps=24, bg_color=(10, 30, 60), text_color="white"):
    img = Image.new("RGB", (1920, 1080), color=bg_color)
    draw = ImageDraw.Draw(img)
    y = 200
    for line in text_lines:
        if line:
            draw.text((200, y), line, fill=text_color)
        y += 50

    tmp_img = str(Path(output_path).with_suffix(".png"))
    img.save(tmp_img)

    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", tmp_img, "-t", str(duration),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), output_path]
    try:
        subprocess.run(cmd, capture_output=True, timeout=30)
    except Exception:
        pass
    Path(tmp_img).unlink(missing_ok=True)
