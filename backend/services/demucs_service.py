"""
Demucs stem separation service.
Handles audio processing and file management.
"""

import logging
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
    
    # Create job-specific output directory
    job_output_dir = SEPARATED_DIR / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Running Demucs on {audio_path}")
    
    try:
        # Use sys.executable to get the current Python (from venv)
        cmd = [
            sys.executable,
            "-m",
            "demucs",
            "--mp3",
            "-d",
            "cuda",
            "-o",
            str(job_output_dir),
            str(audio_path),
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Demucs completed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Demucs failed: {e.stderr}")
        raise RuntimeError(f"Stem separation failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Demucs error: {str(e)}")
        raise RuntimeError(f"Stem separation failed: {str(e)}")
    
    # After Demucs completes, stems are in:
    # separated/{job_id}/htdemucs/{track_name}/
    stems_dir = job_output_dir / "htdemucs"
    
    if not stems_dir.exists():
        raise RuntimeError(f"Demucs output directory not found: {stems_dir}")
    
    # Find the track subdirectory
    subdirs = list(stems_dir.iterdir())
    if not subdirs:
        raise RuntimeError(f"No stem subdirectories found in {stems_dir}")
    
    stems_path = subdirs[0]
    
    logger.info(f"Stem separation complete. Stems at {stems_path}")
    
    return str(stems_path)
