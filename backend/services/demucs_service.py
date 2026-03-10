"""
Demucs stem separation service.
Handles audio processing and file management.
"""

import logging
from pathlib import Path
from demucs.separate import separate

logger = logging.getLogger(__name__)

# Paths
UPLOADS_DIR = Path("uploads")
SEPARATED_DIR = Path("separated")

def separate_stems(job_id: str, filename: str, file_extension: str) -> str:
    """
    Run Demucs stem separation.
    
    Args:
        job_id: Unique job identifier
        filename: Original filename (without extension)
        file_extension: File extension (e.g., ".mp3")
    
    Returns:
        Path to stems directory (e.g., "separated/{job_id}/htdemucs/{filename_without_ext}")
    
    Raises:
        FileNotFoundError: If uploaded file not found
        RuntimeError: If Demucs fails or output not created 
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
        # Run Demucs
        # Demucs saves to out_dir/htdemucs/{track_name} by default

        separate(
            paths=[str(audio_path)],
            out_dir=str(job_output_dir),
            device="cuda",
            shifts=1,
            overlap=0.25,
            jobs=1
        )
    except Exception as e:
        logger.error(f"Demucs failed: {str(e)}")
        raise RuntimeError(f"Stem separation failed: {str(e)}")
    
    # After Demucs completes, stems are in:
    # separated/{job_id}/htdemucs/{original_filename_without_extension}/
    # (e.g., separated/abc-123/htdemucs/song/)

    stems_path = job_output_dir / "htdemucs" / Path(audio_path.stem)

    if not stems_path.exists():
        raise RuntimeError(f"Demucs output not found at expected path: {stems_path}")
    
    logger.info(f"Stem separation complete. Stems at {stems_path}")

    return str(stems_path)




