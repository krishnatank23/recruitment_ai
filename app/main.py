#main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.jd import router as jd_router
from app.api.pipeline import router as pipeline_router
from app.api.cv_analysis import router as cv_router

app = FastAPI(title="Recruitment AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "Backend running"}

# ✅ IMPORTANT: ADD PREFIXES
app.include_router(jd_router, prefix="/jd", tags=["JD"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(cv_router, prefix="/cv", tags=["CV Analysis"])
