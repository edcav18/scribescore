"""
Upload endpoints.
"""

import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from models import job_store
from services.demucs_service import separate_stems

router = APIRouter(prefix="/api", tags=["uploads"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}
MAX_FILE_SIZE_MB = 50

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {suffix} not supported. Use: {ALLOWED_EXTENSIONS}"
        )

    # Generate a unique job ID — everything downstream will use this
    job_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{job_id}{suffix}"

    # Stream to disk (don't load whole file into memory)
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check size after saving
    size_mb = save_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        save_path.unlink()
        raise HTTPException(status_code=400, detail=f"File too large: {size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)")
    
    # Create job in store
    job = job_store.create(job_id, file.filename)

    # Queue stem separation as background task
    if background_tasks:
        background_tasks.add_task(
            separate_stems,
            job_id,
            Path(file.filename).stem,
            suffix
        )


    return {
        "job_id": job_id,
        "filename": file.filename,
        "saved_as": str(save_path),
        "size_mb": round(size_mb, 2),
        "status": "uploaded"
    }

