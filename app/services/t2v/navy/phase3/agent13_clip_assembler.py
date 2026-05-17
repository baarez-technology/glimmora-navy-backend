"""
Agent 13 — Clip Assembler
Combines frames + TTS audio into one MP4 clip per step.
Uses FFmpeg for video assembly and OpenAI TTS for narration.
"""
import subprocess
import tempfile
from pathlib import Path
from openai import OpenAI

client = OpenAI()


def assemble_clip(
    frame_paths: list[str],
    narration_text: str,
    output_path: str,
    fps: int = 24,
    step_num: int = 1,
) -> dict:
    """Assemble frames + TTS narration into one MP4 clip."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Generate TTS narration
    audio_path = str(Path(output_path).with_suffix(".mp3"))
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="alloy",
            input=narration_text[:4096],
        )
        response.stream_to_file(audio_path)
    except Exception as e:
        print(f"[Agent 13] TTS failed: {e}, assembling without audio")
        audio_path = None

    # Create frame list file for FFmpeg
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for frame in frame_paths:
            frame_escaped = frame.replace("\\", "/")
            f.write(f"file '{frame_escaped}'\n")
            f.write(f"duration {1.0 / fps}\n")
        # Repeat last frame
        if frame_paths:
            f.write(f"file '{frame_paths[-1].replace(chr(92), '/')}'\n")
        concat_file = f.name

    # Assemble video from frames
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-vf", f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", str(fps),
    ]

    if audio_path and Path(audio_path).exists():
        cmd.extend(["-i", audio_path, "-c:a", "aac", "-shortest"])

    cmd.append(output_path)

    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[Agent 13] FFmpeg error: {e}")
        return {"clip_path": None, "audio_path": audio_path, "error": str(e)}

    # Cleanup
    Path(concat_file).unlink(missing_ok=True)

    return {
        "clip_path":  output_path if Path(output_path).exists() else None,
        "audio_path": audio_path,
        "frames":     len(frame_paths),
        "step":       step_num,
    }
