"""
Agent 12 — Frame Interpolator
Generates in-between frames from consecutive keyframe pairs using PIL cross-dissolve.
"""
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def interpolate_frames(
    keyframe_paths: list[str],
    output_dir: str,
    frames_between: int = 8,
) -> list[str]:
    """
    Generate interpolated frames between each consecutive keyframe pair.
    Returns ordered list of all frame paths (keyframes + interpolated).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if not PIL_AVAILABLE or len(keyframe_paths) < 2:
        return keyframe_paths

    all_frames = []
    frame_idx = 0

    for i in range(len(keyframe_paths) - 1):
        img_a = Image.open(keyframe_paths[i]).convert("RGBA")
        img_b = Image.open(keyframe_paths[i + 1]).convert("RGBA")

        # Ensure same size
        if img_a.size != img_b.size:
            img_b = img_b.resize(img_a.size, Image.LANCZOS)

        # Add first keyframe
        out_path = str(Path(output_dir) / f"interp_{frame_idx:04d}.png")
        img_a.convert("RGB").save(out_path)
        all_frames.append(out_path)
        frame_idx += 1

        # Generate cross-dissolve interpolated frames
        for j in range(1, frames_between + 1):
            alpha = j / (frames_between + 1)
            blended = Image.blend(img_a, img_b, alpha)
            out_path = str(Path(output_dir) / f"interp_{frame_idx:04d}.png")
            blended.convert("RGB").save(out_path)
            all_frames.append(out_path)
            frame_idx += 1

    # Add the last keyframe
    last = Image.open(keyframe_paths[-1]).convert("RGB")
    out_path = str(Path(output_dir) / f"interp_{frame_idx:04d}.png")
    last.save(out_path)
    all_frames.append(out_path)

    print(f"[Agent 12] Interpolated {len(keyframe_paths)} keyframes -> {len(all_frames)} total frames")
    return all_frames
