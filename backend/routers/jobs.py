"""
Job management endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks

from models import job_store
from services.demucs_service import separate_stems

router = APIRouter(prefix="/api", tags=["jobs"])

logger = logging.getLogger(__name__)

@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Poll for job status.
    
    Returns:
        {
            "job_id": str,
            "filename": str,
            "status": "uploaded" | "processing_stems" | "stems_ready" | "failed",
            "created_at": ISO timestamp,
            "updated_at": ISO timestamp,
            "error_message": str (if failed)
        }
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.to_dict()

@router.post("/jobs/{job_id}/process")
async def process_job(job_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger stem separation for a job.
    (Usually called automatically after upload, but exposed for testing.)
    
    Returns:
        {"status": "processing_started"}
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "uploaded":
        raise HTTPException(
            status_code=400,
            detail=f"Job already processing or complete. Current status: {job.status}"
        )
    
    # Extract filename and extension from job.filename
    # job.filename is the original filename (e.g., "song.mp3")
    from pathlib import Path
    file_path = Path(job.filename)
    filename_no_ext = file_path.stem
    extension = file_path.suffix

    # Queue background task
    background_tasks.add_task(
        separate_stems,
        job_id,
        filename_no_ext,
        extension
    )