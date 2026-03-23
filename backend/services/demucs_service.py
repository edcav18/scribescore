"""
Demucs stem separation service.
Handles audio processing and file management.
"""

import logging
from models import job_store
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Paths
UPLOADS_DIR = Path("uploads")
SEPARATED_DIR = Path("separated")


def separate_stems(job_id: str, filename: str, file_extension: str) -> str:
    """
    Run Demucs stem separation via command line.
    Uses the current Python interpreter (from venv).
    """
    # Path to uploaded audio
    audio_path = UPLOADS_DIR / f"{job_id}{file_extension}"
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Uploaded file not found: {audio_path}")
    
    logger.info(f"Running Demucs on {audio_path}")
    
    try:
        # Update status to processing
        job_store.update_status(job_id, "processing_stems")

        # Use sys.executable to get the current Python (from venv)
        cmd = [
            sys.executable,
            "-m",
            "demucs",
            "--mp3",
            "-d",
            "cuda",
            "-o",
            str(SEPARATED_DIR),
            "--shifts",
            "4",  # Instead of default 1
            str(audio_path),
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Demucs completed successfully")

        # Update status to ready
        job_store.update_status(job_id, "stems_ready")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Demucs failed: {e.stderr}")
        job_store.update_status(job_id, "failed", error_message=e.stderr)
        raise RuntimeError(f"Stem separation failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Demucs error: {str(e)}")
        raise RuntimeError(f"Stem separation failed: {str(e)}")
    
    # After Demucs completes, stems are in:
    # separated/{job_id}/htdemucs/{track_name}/
    stems_dir = SEPARATED_DIR / "htdemucs" / job_id
    
    if not stems_dir.exists():
        raise RuntimeError(f"Demucs output directory not found: {stems_dir}")
    
    # Find the track subdirectory
    stem_file = stems_dir / "other.wav"
    if not stem_file.exists():
        raise RuntimeError(f"Guitar stem not found: {stem_file}")
    
    logger.info(f"Stem separation complete. Stems at {stems_dir}")
    
    return str(stems_dir)
