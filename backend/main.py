from dotenv import load_dotenv
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers import uploads, jobs

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Music Transcriber")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(uploads.router)
app.include_router(jobs.router)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
