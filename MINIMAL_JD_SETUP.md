# Minimal JD Generation Setup

## Essential Files for JD Generation Only

### **1. Backend (app/)**

#### Core Files Needed:
- `main.py` - FastAPI entry point ✅
- `api/jd.py` - JD endpoints
- `api/pipeline.py` - Pipeline for /run_pipeline
- `agents/jd_clarifier.py` - Clarifying questions
- `agents/profile_builder.py` - Build ideal candidate profile
- `agents/jd_generator.py` - Generate JD
- `agents/jd_chatbot.py` - Refine JD
- `utils/llm.py` - LLM calls (Groq)
- `utils/constants.py` - App constants
- `utils/google_form_loader.py` - Load roles from Google Sheet
- `utils/file_export.py` - Export JD to DOCX/PDF
- `utils/text_cleanup.py` - Text cleanup utilities

### **2. Frontend (ui/)**

#### Core Files Needed:
- `streamlit_app.py` - Main app entry
- `recruiter_portal.py` - Recruiter workflow (6 steps)

### **3. Files to DELETE (NOT NEEDED)**

#### Candidate/Resume Processing:
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
- `agents/export_agent.py` (not needed for JD)
- `agents/jd_parser.py`

#### UI:
- `ui/candidate_portal.py`

#### API:
- `api/candidates.py`
- `api/outreach.py`

#### Database:
- `db/postgres.py`
- `db/vector_store.py`

#### Graph:
- `graphs/recruitment_graph.py`
- `graphs/state.py`

#### Utils:
- `utils/resume_skills.py`
- `utils/form_mapper.py`

---

## Workflow Flow (6 Steps)

```
RECRUITER PORTAL
├─ Step 1: Select role (from Google Sheet)
│  └─ uses: google_form_loader.py
│
├─ Step 2: Clarify role (MCQs)
│  └─ uses: jd_clarifier.py → LLM generates 5 clarifying questions
│
├─ Step 3: Build profile (ideal candidate)
│  └─ uses: profile_builder.py → LLM builds structured profile from clarifications
│
├─ Step 4: Draft JD
│  └─ uses: jd_generator.py → LLM generates JD from profile
│
├─ Step 5: Refine JD (chat loop)
│  └─ uses: jd_chatbot.py → LLM refines JD based on instructions
│
└─ Step 6: Export (DOCX/PDF)
   └─ uses: file_export.py → exports final JD
```

---

## API Endpoints

### POST `/jd/generate`
**Request:**
```json
{
  "form_data": {
    "role": "Data Engineer",
    "department": "Engineering",
    "experience": "5-8 years",
    "employment_type": "Full-time",
    "location": "India",
    ...
  },
  "profile": {
    "role": "Data Engineer",
    "department": "Engineering",
    "executive_summary": "...",
    ...
  }
}
```

**Response:**
```json
{
  "jd": "# Data Engineer\n\n## About Us\n...",
  "success": true
}
```

---

## Backend Start

```bash
cd recruitment_ai
source venv/bin/activate  # or on Windows: venv\Scripts\activate

python -m uvicorn app.main:app --reload --port 8000
```

## Frontend Start

```bash
cd recruitment_ai
source venv/bin/activate  # or on Windows: venv\Scripts\activate

python -m streamlit run ui/streamlit_app.py
```

---

## Key Points

1. **No Resume Processing** - This is JD generation only
2. **No Candidate Matching** - No personas, no candidate evaluation
3. **No Database** - Uses only Google Sheet for role data
4. **LLM Only** - All intelligence comes from LLM (Groq)
5. **Simple Flow** - 6 steps from role selection to JD export

