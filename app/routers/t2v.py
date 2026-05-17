import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User
from app.services import t2v_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/t2v", tags=["Text-to-Video"])

class T2VRequest(BaseModel):
    question: str
    domain: Literal["navy"] = "navy"

@router.post("/generate", summary="Start video generation")
async def t2v_generate(
    req: T2VRequest,
    current_user: User = Depends(get_current_user)
):
    """Start the multi-agent text-to-video pipeline for a specific question."""
    job_id = await t2v_service.start_generation(req.question, req.domain)
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Video generation started. Poll /api/t2v/status/{job_id}",
    }

@router.get("/status/{job_id}", summary="Check generation status")
async def t2v_status(job_id: str, current_user: User = Depends(get_current_user)):
    """Check the status and progress of a video generation job."""
    status = t2v_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, **status}

@router.get("/video/{domain}/{session_id}", summary="Serve generated video")
async def t2v_video(domain: Literal["navy"], session_id: str):
    """Download or stream a generated MP4 video."""
    video_path = t2v_service.get_video_path(domain, session_id)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(
        str(video_path), 
        media_type="video/mp4", 
        filename=f"aegis_{domain}_{session_id}.mp4"
    )

@router.get("/jobs", summary="List all jobs")
async def t2v_jobs(current_user: User = Depends(get_current_user)):
    """List all recent video generation jobs."""
    return t2v_service.get_all_jobs()

@router.get("/training-modules/{domain}", summary="List available modules")
async def training_modules(domain: Literal["navy"]):
    """Return validated training modules available for video generation."""
    try:
        modules = t2v_service.get_training_modules(domain)
        return {
            "domain": domain,
            "modules": modules,
            "total_validated": len(modules),
            "pipeline_version": "2.0.0",
        }
    except Exception as e:
        logger.error(f"Error fetching training modules: {str(e)}")
        return {"domain": domain, "modules": [], "error": str(e)}
