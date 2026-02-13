# JD Generation Clean Code Setup

## 1. app/api/jd.py (CLEAN VERSION)

```python
# app/api/jd.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.jd_generator import generate_jd
from app.agents.jd_clarifier import generate_clarifying_questions
from app.agents.jd_chatbot import refine_jd
from app.agents.profile_builder import build_profile
import json

router = APIRouter()

class ClarifyRequest(BaseModel):
    form_data: dict

class ProfileRequest(BaseModel):
    form_data: dict
    answers: list

class JDGenerateRequest(BaseModel):
    form_data: dict
    profile: dict = None

class RefineRequest(BaseModel):
    jd: str
    instruction: str
    role: str = ""
    session_id: str = ""

@router.post("/clarify")
async def clarify_jd_api(request: ClarifyRequest):
    """Generate clarifying questions from form data."""
    try:
        questions = generate_clarifying_questions(form_data=request.form_data)
        
        if isinstance(questions, str):
            questions = json.loads(questions)
        
        return {"success": True, "questions": questions}
    except Exception as e:
        return {"success": False, "error": str(e), "questions": []}

@router.post("/profile")
async def profile_builder_api(request: ProfileRequest):
    """Build ideal candidate profile from clarifications."""
    try:
        profile = build_profile(
            form_data=request.form_data,
            clarification_answers=request.answers
        )
        return {"success": True, "profile": profile}
    except Exception as e:
        return {"success": False, "error": str(e), "profile": {}}

@router.post("/generate")
async def generate_jd_api(request: JDGenerateRequest):
    """Generate JD from profile and form data."""
    try:
        jd = generate_jd(
            form_data=request.form_data,
            profile=request.profile
        )
        return {"success": True, "jd": jd}
    except Exception as e:
        return {"success": False, "error": str(e), "jd": ""}

@router.post("/refine")
async def refine_jd_api(request: RefineRequest):
    """Refine JD based on user instruction."""
    try:
        updated_jd = refine_jd(
            current_jd=request.jd,
            instruction=request.instruction,
            role=request.role,
            session_id=request.session_id
        )
        return {"success": True, "jd": updated_jd}
    except Exception as e:
        return {"success": False, "error": str(e), "jd": request.jd}
```

---

## 2. app/api/pipeline.py (CLEAN VERSION FOR JD ONLY)

```python
# app/api/pipeline.py
from fastapi import APIRouter
import json

router = APIRouter()

@router.post("/run_pipeline")
async def run_jd_pipeline(form_data: dict, profile: dict = None):
    """
    Simple JD generation pipeline.
    
    Step 1: Generate clarifying questions
    Step 2: Build ideal candidate profile
    Step 3: Generate JD
    
    Input:
    {
        "form_data": {...form data...},
        "clarification_answers": [...answers...]
    }
    
    Returns: {"jd": "...", "export_path": "..."}
    """
    try:
        from app.agents.jd_generator import generate_jd
        from app.agents.profile_builder import build_profile
        from app.utils.file_export import export_to_docx, export_to_pdf
        
        print("[JD_PIPELINE] Starting JD generation...")
        
        # Step 1: Build profile if not provided
        if not profile:
            print("[JD_PIPELINE] Building profile...")
            clarification_answers = form_data.get("clarification_answers", [])
            profile = build_profile(
                form_data=form_data,
                clarification_answers=clarification_answers
            )
        
        # Step 2: Generate JD
        print("[JD_PIPELINE] Generating JD...")
        jd = generate_jd(form_data=form_data, profile=profile)
        
        # Step 3: Export (optional)
        print("[JD_PIPELINE] Exporting JD...")
        role = form_data.get("role", "JD")
        docx_path = export_to_docx(jd, role.replace(" ", "_"))
        
        print("[JD_PIPELINE] Pipeline complete!")
        
        return {
            "success": True,
            "jd": jd,
            "export_path": docx_path,
            "profile": profile
        }
        
    except Exception as e:
        print(f"[JD_PIPELINE] Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "jd": "",
            "export_path": None,
            "profile": {}
        }
```

---

## 3. app/main.py (CLEAN VERSION)

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.jd import router as jd_router
from app.api.pipeline import router as pipeline_router

app = FastAPI(
    title="JD Generation API",
    description="Generate Job Descriptions using LLM",
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
        "service": "JD Generation API",
        "version": "1.0"
    }

# Include routers
app.include_router(jd_router, prefix="/jd", tags=["JD Generation"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
```

---

## 4. Streamlit UI File Structure (ui/recruiter_portal.py - CLEAN)

The recruiter portal should only have 6 steps:
1. Select role
2. Clarify role (question answers)
3. Build profile
4. Draft JD
5. Refine JD (chat)
6. Export JD

**No resume upload, no candidate matching, no personas.**

---

## What to DELETE

### Agents to Delete:
- `agents/resume_parser.py`
- `agents/evaluator.py`
- `agents/job_fit_evaluator.py`
- `agents/candidate_intel.py`
- `agents/matcher.py`
- `agents/ranking.py`
- `agents/scoring.py`
- `agents/semantic_matcher.py`
- `agents/persona_builder.py`
- `agents/persona_matcher.py`
- `agents/whatsapp_agent.py`
- `agents/export_agent.py`
- `agents/jd_parser.py`

### API to Delete:
- `api/candidates.py`
- `api/outreach.py`

### UI to Delete:
- `ui/candidate_portal.py`

### DB to Delete:
- `db/postgres.py`
- `db/vector_store.py`

### Graph to Delete:
- `graphs/recruitment_graph.py`
- `graphs/state.py`

### Utils to Delete:
- `utils/resume_skills.py`
- `utils/form_mapper.py`

---

## Required Dependencies (keep in requirements.txt)

```
python-dotenv
langchain
langchain-groq
fastapi
uvicorn
streamlit
pandas
openpyxl
pydantic
python-docx
reportlab
pdfplumber
gspread
google-auth-oauthlib
google-auth-httplib2
```

---

## Environment Variables Needed (.env)

```
GROQ_API_KEY=your_groq_key
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_CREDENTIALS_JSON=path_to_credentials.json
```

