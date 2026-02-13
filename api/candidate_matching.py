# candidate_matching.py - API endpoints for candidate matching
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os

from app.agents.persona_builder import generate_personas
from app.agents.resume_parser import parse_candidate_resumes
from app.agents.candidate_matcher import match_candidates_to_personas, get_best_matches

router = APIRouter()

class GeneratePersonasRequest(BaseModel):
    """Request to generate personas from job profile."""
    job_profile: str
    max_personas: int = 5

class MatchRequest(BaseModel):
    """Request to match candidates."""
    candidates: list  # List of {name, resume_text}
    personas: list    # List of persona dicts

@router.post("/generate_personas")
async def generate_personas_api(request: GeneratePersonasRequest):
    """
    Generate 5 personas from a job profile.
    
    Request:
    {
        "job_profile": "Senior Software Engineer with 5+ years..."
    }
    
    Response:
    {
        "success": true,
        "personas": [...],
        "count": 5
    }
    """
    try:
        print(f"[CANDIDATE_MATCHING_API] Generating personas from profile...")
        
        result = generate_personas(request.job_profile)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate personas"),
                "personas": [],
                "count": 0
            }
        
        return {
            "success": True,
            "personas": result.get("personas", []),
            "count": result.get("count", 0),
            "message": f"Generated {result.get('count', 0)} personas"
        }
        
    except Exception as e:
        print(f"[CANDIDATE_MATCHING_API] Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "personas": [],
            "count": 0
        }

@router.post("/match_candidates")
async def match_candidates_api(request: MatchRequest):
    """
    Match candidates to personas.
    
    Request:
    {
        "candidates": [
            {"name": "John Doe", "resume_text": "..."},
            {"name": "Jane Smith", "resume_text": "..."}
        ],
        "personas": [
            {
                "persona_id": 1,
                "name": "Senior Lead",
                "background": "...",
                "key_strengths": [...],
                ...
            }
        ]
    }
    
    Response:
    {
        "success": true,
        "matches": [
            {
                "candidate_name": "John Doe",
                "persona_matches": [
                    {
                        "persona_name": "Senior Lead",
                        "match_score": 85,
                        "match_percentage": "85%",
                        "reasoning": "..."
                    }
                ]
            }
        ]
    }
    """
    try:
        print(f"[CANDIDATE_MATCHING_API] Matching {len(request.candidates)} candidates to {len(request.personas)} personas...")
        
        results = match_candidates_to_personas(request.candidates, request.personas)
        
        return {
            "success": results.get("success", False),
            "matches": results.get("matches", []),
            "total_candidates": results.get("total_candidates", 0),
            "total_personas": results.get("total_personas", 0),
            "error": results.get("error", None)
        }
        
    except Exception as e:
        print(f"[CANDIDATE_MATCHING_API] Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "matches": []
        }

@router.post("/parse_resumes")
async def parse_resumes_api(resumes: List[UploadFile] = File(...)):
    """
    Parse multiple resume files (PDF, DOCX, TXT, ZIP).
    
    Response:
    {
        "success": true,
        "candidates": [
            {
                "candidate_id": 1,
                "name": "resume_filename.pdf",
                "resume_text": "...",
                "file_path": "/tmp/..."
            }
        ],
        "total": 3
    }
    """
    try:
        print(f"[CANDIDATE_MATCHING_API] Parsing {len(resumes)} uploaded file(s)...")
        
        temp_paths = []
        
        # Save uploaded files to temp directory
        temp_dir = tempfile.mkdtemp()
        for upload_file in resumes:
            temp_path = os.path.join(temp_dir, upload_file.filename)
            
            with open(temp_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)
            
            temp_paths.append(temp_path)
            print(f"[CANDIDATE_MATCHING_API] Saved: {upload_file.filename}")
        
        # Parse resumes
        result = parse_candidate_resumes(temp_paths)
        
        return {
            "success": result.get("success", False),
            "candidates": result.get("candidates", []),
            "total": result.get("total", 0),
            "error": result.get("error", None)
        }
        
    except Exception as e:
        print(f"[CANDIDATE_MATCHING_API] Error parsing resumes: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "candidates": [],
            "total": 0
        }

@router.post("/run_full_match")
async def run_full_match_api(
    job_profile: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    """
    Full candidate matching pipeline:
    1. Parse resumes
    2. Generate personas from job profile
    3. Match candidates to personas
    
    Response:
    {
        "success": true,
        "personas": [...],
        "matches": [...],
        "best_matches": {...}
    }
    """
    try:
        print("[CANDIDATE_MATCHING_API] Starting full matching pipeline...")
        
        temp_dir = tempfile.mkdtemp()
        temp_paths = []
        
        # STEP 1: Save and parse resumes
        print("[CANDIDATE_MATCHING_API] Step 1: Parsing resumes...")
        
        for upload_file in resumes:
            temp_path = os.path.join(temp_dir, upload_file.filename)
            with open(temp_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)
            temp_paths.append(temp_path)
        
        candidate_result = parse_candidate_resumes(temp_paths)
        if not candidate_result.get("success"):
            return {
                "success": False,
                "error": candidate_result.get("error", "Failed to parse resumes"),
                "personas": [],
                "matches": []
            }
        
        # STEP 2: Generate personas
        print("[CANDIDATE_MATCHING_API] Step 2: Generating personas...")
        
        persona_result = generate_personas(job_profile)
        if not persona_result.get("success"):
            return {
                "success": False,
                "error": persona_result.get("error", "Failed to generate personas"),
                "personas": [],
                "matches": []
            }
        
        personas = persona_result.get("personas", [])
        
        # STEP 3: Match candidates
        print("[CANDIDATE_MATCHING_API] Step 3: Matching candidates to personas...")
        
        candidates = candidate_result.get("candidates", [])
        match_result = match_candidates_to_personas(candidates, personas)
        
        if not match_result.get("success"):
            return {
                "success": False,
                "error": match_result.get("error", "Failed to match candidates"),
                "personas": personas,
                "matches": []
            }
        
        # Get best matches
        best_matches = get_best_matches(match_result, top_n=5)
        
        print("[CANDIDATE_MATCHING_API] Pipeline complete!")
        
        return {
            "success": True,
            "personas": personas,
            "matches": match_result.get("matches", []),
            "best_matches": best_matches,
            "total_candidates": len(candidates),
            "total_personas": len(personas)
        }
        
    except Exception as e:
        print(f"[CANDIDATE_MATCHING_API] Error in full pipeline: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "personas": [],
            "matches": []
        }
