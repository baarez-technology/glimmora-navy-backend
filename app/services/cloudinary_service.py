"""
Cloudinary storage service for GLIMMORA AEGIS Navy T2V pipeline.
Handles upload and management of generated training videos.
"""
import logging
from pathlib import Path
from typing import Optional

import cloudinary
import cloudinary.uploader
import cloudinary.api

from app.config import settings

logger = logging.getLogger(__name__)

# ── Configure Cloudinary SDK once at import time ─────────────────────────────
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

FOLDER = "aegis/t2v"  # Cloudinary folder prefix


def upload_video(local_path: str | Path, session_id: str, domain: str = "navy") -> Optional[str]:
    """
    Upload a local MP4 to Cloudinary and return the secure public URL.

    Args:
        local_path: Absolute path to the final_video.mp4 on disk.
        session_id: T2V session identifier (used as the public_id).
        domain:     Domain label (e.g. "navy") — used in folder path.

    Returns:
        The secure HTTPS URL from Cloudinary, or None on failure.
    """
    local_path = Path(local_path)
    if not local_path.exists():
        logger.error(f"[Cloudinary] File not found: {local_path}")
        return None

    public_id = f"{FOLDER}/{domain}/{session_id}"

    try:
        logger.info(f"[Cloudinary] Uploading {local_path} → {public_id}")
        result = cloudinary.uploader.upload(
            str(local_path),
            resource_type="video",
            public_id=public_id,
            overwrite=True,
            chunk_size=6_000_000,   # 6 MB chunks for large videos
        )
        url: str = result["secure_url"]
        logger.info(f"[Cloudinary] Upload complete: {url}")
        return url
    except Exception as e:
        logger.error(f"[Cloudinary] Upload failed for session {session_id}: {e}")
        return None


def delete_video(session_id: str, domain: str = "navy") -> bool:
    """Delete a previously uploaded video from Cloudinary."""
    public_id = f"{FOLDER}/{domain}/{session_id}"
    try:
        cloudinary.uploader.destroy(public_id, resource_type="video")
        logger.info(f"[Cloudinary] Deleted {public_id}")
        return True
    except Exception as e:
        logger.error(f"[Cloudinary] Delete failed for {public_id}: {e}")
        return False


def is_configured() -> bool:
    """Return True if Cloudinary credentials are present."""
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )
