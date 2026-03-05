"""
Job models for tracking transcription pipeline state.
Week 2: In-memory only. Week 3: Migrate to SQLite.
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime, UTC

@dataclass
class Job:
    job_id: str
    filename: str
    status: str # uploaded, processing_stems, stems_ready, completed, failed
    created_at: str
    updated_at: str
    error_message: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class JobStore:
    """Simple in-memory store for Job objects. Replace with SQLite in Week 3."""

    def __init__(self):
        self.jobs = {}
    
    def create(self, job_id: str, filename: str) -> Job:
        """Create a new job with 'uploaded' status."""
        now = datetime.now(UTC).isoformat
        job = Job(
            job_id=job_id,
            filename=filename,
            status="uploaded",
            created_at=now,
            updated_at=now
        )
        self.jobs[job_id] = job
        return job
    
    def get(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID"""
        return self.jobs.get(job_id)
    
    def update_status(self, job_id: str, status: str, error_message: Optional[str] = None):
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = status
        job.updated_at = datetime.now(UTC).isoformat
        if error_message:
            job.error_messsage = error_message

        return job
    
# Global store instance
job_store = JobStore()
