from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
from pathlib import Path

app = FastAPI(title="AI Music Transcriber")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}
MAX_FILE_SIZE_MB = 50


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
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

    return {
        "job_id": job_id,
        "filename": file.filename,
        "saved_as": str(save_path),
        "size_mb": round(size_mb, 2),
        "status": "uploaded"
    }
