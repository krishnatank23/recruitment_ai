# pipeline.py - JD Generation Pipeline (Minimal Setup)
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import json

router = APIRouter()

class JDGenerationRequest(BaseModel):
    """Request body for JD generation pipeline."""
    form_data: dict
    clarification_answers: list = []
    profile: Optional[dict] = None

@router.post("/run_pipeline")
async def run_jd_pipeline(request: JDGenerationRequest):
    """
    JD Generation Pipeline (Minimal Setup)
    
    Steps:
    1. Build ideal candidate profile (from form_data + clarifications)
    2. Generate JD (from profile + form_data)
    3. Export to DOCX
    
    Request:
    {
        "form_data": {role, department, location, ...},
        "clarification_answers": [{question, answer}, ...],
        "profile": {...} (optional - if pre-built)
    }
    
    Returns:
    {
        "success": bool,
        "jd": "markdown JD",
        "export_path": "/exports/...",
        "profile": {...}
    }
    """
    try:
        from app.agents.jd_generator import generate_jd
        from app.agents.profile_builder import build_profile
        from app.utils.file_export import export_to_docx
        
        print("[JD_PIPELINE] Starting JD generation pipeline...")
        
        # ==================== STEP 1: BUILD PROFILE ====================
        if not request.profile:
            print("[JD_PIPELINE] Step 1: Building ideal candidate profile...")
            try:
                profile = build_profile(
                    form_data=request.form_data,
                    clarification_answers=request.clarification_answers
                )
                print(f"[JD_PIPELINE] Step 1: Profile built successfully")
                print(f"[JD_PIPELINE] Profile keys: {list(profile.keys())}")
            except Exception as e:
                print(f"[JD_PIPELINE] Step 1 ERROR: {str(e)}")
                raise
        else:
            profile = request.profile
            print("[JD_PIPELINE] Step 1: Using pre-built profile")
        
        # ==================== STEP 2: GENERATE JD ====================
        print("[JD_PIPELINE] Step 2: Generating JD from profile...")
        try:
            jd = generate_jd(
                form_data=request.form_data,
                profile=profile
            )
            print("[JD_PIPELINE] Step 2: JD generated successfully")
        except Exception as e:
            print(f"[JD_PIPELINE] Step 2 ERROR: {str(e)}")
            raise
        
        # ==================== STEP 3: EXPORT ====================
        print("[JD_PIPELINE] Step 3: Exporting JD to DOCX...")
        try:
            role = request.form_data.get("role", "JobDescription")
            export_path = export_to_docx(jd, role.replace(" ", "_"))
            print(f"[JD_PIPELINE] Step 3: Exported to {export_path}")
        except Exception as e:
            print(f"[JD_PIPELINE] Step 3 WARNING (non-blocking): {str(e)}")
            export_path = None
        
        # ==================== RETURN RESULTS ====================
        print("[JD_PIPELINE] Pipeline complete! ✓")
        
        return {
            "success": True,
            "message": "JD generation complete",
            "jd": jd,
            "export_path": export_path,
            "profile": profile
        }
        
    except Exception as e:
        print(f"[JD_PIPELINE] FATAL ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        return {
            "success": False,
            "message": f"Pipeline failed: {str(e)}",
            "error": str(e),
            "jd": "",
            "export_path": None,
            "profile": {}
        }
