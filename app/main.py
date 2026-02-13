# main.py - FastAPI Backend for JD Generation & Candidate Matching
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.jd import router as jd_router
from app.api.pipeline import router as pipeline_router
from app.api.candidate_matching import router as candidate_matching_router

app = FastAPI(
    title="Recruitment AI - JD Generation & Candidate Matching",
    description="Generate Job Descriptions and Match Candidates using LLM",
    version="1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Recruitment AI",
        "version": "1.0",
        "features": ["JD Generation", "Candidate Matching"]
    }

# Include routers
app.include_router(jd_router, prefix="/jd", tags=["JD Generation"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(candidate_matching_router, prefix="/candidate_matching", tags=["Candidate Matching"])
