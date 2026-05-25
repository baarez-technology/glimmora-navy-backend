import asyncio
import logging
import sys
import time
import traceback
import importlib
from pathlib import Path
from typing import Literal

from app.config import settings

logger = logging.getLogger(__name__)

T2V_ROOT = Path(__file__).parent / "t2v"

# Active jobs tracking
_active_jobs: dict[str, dict] = {}

def _run_generation(job_id: str, question: str, domain: str):
    try:
        # Setup paths for this specific domain
        domain_dir = T2V_ROOT / domain
        
        # Add necessary paths to sys.path
        sys.path.insert(0, str(domain_dir))
        sys.path.insert(0, str(domain_dir / "phase1"))
        sys.path.insert(0, str(domain_dir / "phase2"))
        sys.path.insert(0, str(domain_dir / "phase3"))
        sys.path.insert(0, str(T2V_ROOT)) # For demo_config etc

        _active_jobs[job_id]["status"] = "phase2"
        _active_jobs[job_id]["progress"] = "Analyzing question..."

        # Phase 2
        try:
            module_p2 = importlib.import_module(f"{domain}.phase2.run_phase2")
            run_p2 = module_p2.run
        except ImportError as e:
            raise ImportError(f"Failed to load Phase 2 for domain '{domain}': {str(e)}")

        p2 = run_p2(question)

        _active_jobs[job_id]["status"] = "phase3"
        _active_jobs[job_id]["progress"] = f"Generating video ({p2['summary']['total_steps']} steps)..."

        # Phase 3
        try:
            module_p3 = importlib.import_module(f"{domain}.phase3.run_phase3")
            run_p3 = module_p3.run
        except ImportError as e:
            raise ImportError(f"Failed to load Phase 3 for domain '{domain}': {str(e)}")

        p3 = run_p3(
            validated_steps=p2["steps"],
            question=question,
            use_validator=False,
        )

        video_path = p3["summary"].get("video_path")
        session_id = p3.get("session_id")

        if video_path and Path(video_path).exists():
            # ── Upload to Cloudinary ──────────────────────────────────────
            from app.services import cloudinary_service
            cloudinary_url: str | None = None
            if cloudinary_service.is_configured():
                cloudinary_url = cloudinary_service.upload_video(video_path, session_id, domain)

            _active_jobs[job_id] = {
                "status": "completed",
                "question": question,
                "domain": domain,
                "video_url": cloudinary_url or f"/api/t2v/video/{domain}/{session_id}",
                "cloudinary_url": cloudinary_url,
                "video_path": video_path,
                "session_id": session_id,
                "elapsed_s": p3["summary"]["timings"].get("total"),
                "phase2": p2["summary"],
                "phase3": p3["summary"],
                "steps": [
                    {"step": s["step"], "title": s["title"],
                     "verdict": s.get("validation", {}).get("verdict", "N/A")}
                    for s in p2.get("steps", [])
                ],
            }

        else:
            _active_jobs[job_id] = {
                "status": "failed",
                "question": question,
                "error": "Pipeline completed but no video file produced.",
            }
    except Exception as e:
        logger.error(f"T2V Error for job {job_id}: {str(e)}")
        traceback.print_exc()
        _active_jobs[job_id] = {
            "status": "failed",
            "question": question,
            "error": str(e),
        }
    finally:
        # Clean up sys.path if needed (optional but good practice)
        pass

async def start_generation(question: str, domain: str) -> str:
    job_id = f"job_{int(time.time() * 1000)}"
    _active_jobs[job_id] = {
        "status": "queued",
        "question": question,
        "domain": domain,
        "started_at": time.time(),
        "progress": "Starting pipeline...",
    }

    # Run in executor to not block the event loop
    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        None, _run_generation, job_id, question, domain
    )

    return job_id

def get_job_status(job_id: str):
    return _active_jobs.get(job_id)

def get_all_jobs():
    serializable_jobs = {}
    for job_id, job in _active_jobs.items():
        safe_job = {}
        for k, v in job.items():
            if k == "video_path" and v:
                safe_job[k] = str(v)
            else:
                safe_job[k] = v
        serializable_jobs[job_id] = safe_job
    return serializable_jobs

def get_video_path(domain: str, session_id: str) -> Path:
    return T2V_ROOT / domain / "data" / "output" / session_id / "final_video.mp4"

def get_job_by_session(session_id: str) -> dict | None:
    """Return the completed job dict for a given session_id, or None."""
    for job in _active_jobs.values():
        if job.get("session_id") == session_id:
            return job
    return None

def get_training_modules(domain: str):
    # Add T2V_ROOT to path to import demo_config
    if str(T2V_ROOT) not in sys.path:
        sys.path.insert(0, str(T2V_ROOT))
    
    from demo_config import get_validated_modules
    return get_validated_modules(domain)
