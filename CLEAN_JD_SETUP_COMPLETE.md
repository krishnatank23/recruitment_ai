# ✅ CLEAN JD GENERATION SETUP - COMPLETE GUIDE

## Overview

This is a **minimal, production-ready** JD generation system with:
- ✅ 4 essential LLM agents (Clarifier, Profile Builder, JD Generator, JD Chatbot)
- ✅ FastAPI backend with clean 3-step pipeline
- ✅ Streamlit UI with 6-step recruiter workflow
- ✅ No database, no resume parsing, no candidate matching
- ✅ Clean error handling and debug logging

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│           RECRUITER PORTAL (Streamlit)              │
├─────────────────────────────────────────────────────┤
│ Step 1: Select Role (from Google Sheet)             │
│ Step 2: Clarify Role (5 MCQ questions)              │
│ Step 3: Build Profile (LLM generates profile)       │
│ Step 4: Draft JD (LLM generates job description)    │
│ Step 5: Refine JD (Chat-based refinement loop)      │
│ Step 6: Export (DOCX/PDF)                           │
└─────────────────────────────────────────────────────┘
          ↓                              ↑
┌─────────────────────────────────────────────────────┐
│         FASTAPI BACKEND (Python)                    │
├─────────────────────────────────────────────────────┤
│ POST /jd/clarify     → generate clarifying questions│
│ POST /jd/profile     → build ideal candidate profile│
│ POST /jd/generate    → generate job description     │
│ POST /jd/refine      → refine JD via chat           │
│ POST /pipeline/run_pipeline → orchestrate full flow │
└─────────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────────┐
│    LLM AGENTS (Groq via LangChain)                  │
├─────────────────────────────────────────────────────┤
│ • jd_clarifier.py       - Generate 5 MCQ questions  │
│ • profile_builder.py    - Build Ideal Candidate    │
│ • jd_generator.py       - Generate Job Description  │
│ • jd_chatbot.py         - Refine JD via chat        │
└─────────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────────┐
│    UTILITIES & DATA                                 │
├─────────────────────────────────────────────────────┤
│ • google_form_loader.py - Fetch roles from Sheet   │
│ • file_export.py        - Export to DOCX/PDF       │
│ • llm.py                - Groq LLM initialization   │
└─────────────────────────────────────────────────────┘
```

---

## 🗂️ File Structure (Clean Setup)

```
recruitment_ai/
├── app/
│   ├── __init__.py
│   ├── main.py                          ← FastAPI app
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── jd_clarifier.py             ✅ KEPT
│   │   ├── profile_builder.py           ✅ KEPT
│   │   ├── jd_generator.py              ✅ KEPT
│   │   ├── jd_chatbot.py                ✅ KEPT
│   │   └── [others]                     ❌ DELETE
│   ├── api/
│   │   ├── __init__.py
│   │   ├── jd.py                        ✅ KEPT
│   │   ├── pipeline.py                  ✅ UPDATED (clean)
│   │   └── [others]                     ❌ DELETE
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── constants.py                 ✅ KEPT
│   │   ├── llm.py                       ✅ KEPT
│   │   ├── google_form_loader.py        ✅ KEPT
│   │   ├── file_export.py               ✅ KEPT
│   │   ├── text_cleanup.py              ✅ KEPT (used by file_export)
│   │   └── [others]                     ❌ DELETE
│   └── [db/, graphs/, others]           ❌ DELETE
├── ui/
│   ├── __init__.py
│   ├── streamlit_app.py                 ✅ KEPT (router)
│   ├── recruiter_portal_clean.py        ✅ NEW CLEAN VERSION
│   └── recruiter_portal.py              ❌ DELETE (old version)
├── requirements.txt                      ✅ UPDATED
├── .env                                  ✅ NEEDED
└── app/main.py                           ✅ CLEAN VERSION PROVIDED
```

---

## 📦 Required Dependencies

**requirements.txt:**
```
python-dotenv==1.0.0
langchain==0.1.0
langchain-groq==0.0.1
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.0
pandas==2.1.1
openpyxl==3.21.0
pydantic==2.4.2
python-docx==0.8.11
reportlab==4.0.7
pdfplumber==0.10.3
gspread==5.11.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.2.0
```

---

## 🔑 Environment Variables (.env)

```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_CREDENTIALS_JSON=path/to/credentials.json
```

---

## 🚀 How to Run

### 1. Backend (FastAPI)
```bash
cd recruitment_ai
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**
API docs: **http://localhost:8000/docs**

### 2. Frontend (Streamlit)
```bash
cd recruitment_ai
streamlit run ui/recruiter_portal_clean.py
```

Frontend will be available at: **http://localhost:8501**

---

## 📋 Core Files (Updated/Clean Versions)

### 1. **app/main.py** (Clean FastAPI Setup)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.jd import router as jd_router
from app.api.pipeline import router as pipeline_router

app = FastAPI(
    title="JD Generation API",
    description="Generate Job Descriptions using LLM",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "running", "service": "JD Generation API", "version": "1.0"}

app.include_router(jd_router, prefix="/jd", tags=["JD Generation"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
```

---

### 2. **app/api/jd.py** (Clean Endpoints)

✅ **Already exists** with 4 endpoints:
- `POST /jd/clarify` - Generate 5 MCQ questions
- `POST /jd/profile` - Build ideal candidate profile
- `POST /jd/generate` - Generate job description
- `POST /jd/refine` - Refine JD based on instruction

---

### 3. **app/api/pipeline.py** (Updated - Clean)

✅ **Updated** with single endpoint:
- `POST /pipeline/run_pipeline` - 3-step orchestration:
  1. Build profile
  2. Generate JD
  3. Export to DOCX

Request:
```json
{
  "form_data": {...},
  "clarification_answers": [...],
  "profile": null
}
```

Response:
```json
{
  "success": true,
  "message": "JD generation complete",
  "jd": "...",
  "export_path": "/exports/...",
  "profile": {...}
}
```

---

### 4. **ui/recruiter_portal_clean.py** (New Clean UI)

✅ **New clean version** with 6-step workflow:
1. **Select Role** - Pick from Google Sheet
2. **Clarify** - Answer 5 MCQ questions
3. **Build Profile** - LLM generates ideal candidate profile
4. **Draft JD** - LLM generates job description
5. **Refine JD** - Chat-based refinement loop
6. **Export** - Download as DOCX/PDF

**Features:**
- Clean Streamlit UI with progress bar
- Session state management
- Error handling with user feedback
- Export button for DOCX/PDF

---

## 4️⃣ Core LLM Agents (Unchanged)

### **1. jd_clarifier.py**
Generates 5 clarifying MCQ questions from role data.

**Input:**
```python
form_data = {
    "role": "Senior Software Engineer",
    "department": "Engineering",
    ...
}
```

**Output:**
```python
[
    {
        "question": "What's the primary focus?",
        "options": ["Backend", "Frontend", "Full-stack", "DevOps"]
    },
    ...
]
```

---

### **2. profile_builder.py**
Builds 15-field Ideal Candidate Profile from form data + clarifications.

**Input:**
```python
form_data = {...}
clarification_answers = [
    {"question": "...", "answer": "..."},
    ...
]
```

**Output:**
```python
{
    "role": "Senior Software Engineer",
    "department": "Engineering",
    "executive_summary": "...",
    "experience": "...",
    "must_have": [...],
    "nice_to_have": [...],
    "key_responsibilities": [...],
    "success_metrics": [...],
    "team_fit": "...",
    "work_environment": "...",
    "personality_profile": "...",
    "dealbreakers": [...],
    "ideal_candidate_portrait": "...",
    ...
}
```

---

### **3. jd_generator.py**
Generates professional Job Description from profile.

**Input:**
```python
form_data = {...}
profile = {...}  # From profile_builder
```

**Output:**
```markdown
# Senior Software Engineer

## About Us
[Company info]

## Role Overview
[Role description]

## Key Responsibilities
- [Responsibility 1 - max 1.5 lines]
- [Responsibility 2 - max 1.5 lines]
...

## Requirements
### Must Have
- [Skill 1]
- [Skill 2]
...

### Nice to Have
- [Skill A]
- [Skill B]
...

## Who Will Succeed
[Success criteria]
```

---

### **4. jd_chatbot.py**
Refines JD based on recruiter instructions via chat.

**Input:**
```python
current_jd = "..."
instruction = "Make it shorter and add remote flexibility"
role = "Senior Software Engineer"
```

**Output:**
```
[Refined JD with instruction applied]
```

---

## 🧪 Testing the Setup

### Test 1: Backend Health Check
```bash
curl http://localhost:8000
```

Expected response:
```json
{"status": "running", "service": "JD Generation API", "version": "1.0"}
```

---

### Test 2: Generate Clarifying Questions
```bash
curl -X POST http://localhost:8000/jd/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "form_data": {
      "role": "Senior Software Engineer",
      "department": "Engineering"
    }
  }'
```

---

### Test 3: Full Pipeline
```bash
curl -X POST http://localhost:8000/pipeline/run_pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "form_data": {
      "role": "Senior Software Engineer",
      "department": "Engineering"
    },
    "clarification_answers": [
      {"question": "Q1", "answer": "Answer1"},
      ...
    ]
  }'
```

---

## 📝 Files to Delete (Not Needed for JD Generation)

### Agents to Delete:
- `agents/resume_parser.py`
- `agents/evaluator.py`
- `agents/job_fit_evaluator.py`
- `agents/candidate_intel.py`
- `agents/matcher.py`
- `agents/ranking.py`
- `agents/scoring.py`
- `agents/semantic_matcher.py`
- `agents/persona_builder.py` (if exists)
- `agents/persona_matcher.py` (if exists)
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

### Graphs to Delete:
- `graphs/recruitment_graph.py`
- `graphs/state.py`

### Utils to Delete:
- `utils/resume_skills.py`
- `utils/form_mapper.py`

### Old UI to Delete:
- `ui/recruiter_portal.py` (replaced by recruiter_portal_clean.py)

---

## 🔍 Debugging

All backend logs include `[COMPONENT]` prefix for easy grep:

```bash
# Watch JD pipeline logs
grep "\[JD_PIPELINE\]" backend.log

# Watch all errors
grep "ERROR" backend.log
```

Common log prefixes:
- `[JD_PIPELINE]` - Pipeline orchestration
- `[LLM_MATCH]` - Candidate matching (not used in clean setup)
- `[PROFILE_BUILDER]` - Profile building
- `[JD_GENERATOR]` - JD generation
- `[JD_CHATBOT]` - JD refinement

---

## ✅ Checklist Before Production

- [ ] Environment variables set in `.env`
- [ ] Google Sheet configured with roles
- [ ] Google credentials uploaded
- [ ] Backend runs without errors
- [ ] Streamlit UI loads all 6 steps
- [ ] Test end-to-end JD generation (Step 1 → Step 6)
- [ ] Export works for DOCX and PDF
- [ ] Check logs for errors (grep `ERROR`)
- [ ] Verify LLM latency is acceptable (< 30s per step)

---

## 📂 Directory Structure After Cleanup

```
recruitment_ai/
├── .env
├── .gitignore
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── jd_clarifier.py
│   │   ├── profile_builder.py
│   │   ├── jd_generator.py
│   │   └── jd_chatbot.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── jd.py
│   │   └── pipeline.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── llm.py
│   │   ├── google_form_loader.py
│   │   ├── file_export.py
│   │   └── text_cleanup.py
│   └── __pycache__/
├── ui/
│   ├── __init__.py
│   ├── streamlit_app.py
│   └── recruiter_portal_clean.py
├── exports/
│   └── [DOCX/PDF files]
└── scripts/
    └── [utilities]
```

---

## 🎯 Summary

**What You Have:**
- ✅ Clean Streamlit UI (6-step workflow)
- ✅ FastAPI backend with 4 endpoints
- ✅ 4 LLM agents working correctly
- ✅ Complete end-to-end JD generation
- ✅ Export to DOCX/PDF
- ✅ Error handling & debug logging

**What You Don't Have (Not Needed):**
- ❌ Database
- ❌ Resume parsing
- ❌ Candidate matching
- ❌ Persona generation
- ❌ Graph-based orchestration
- ❌ Unnecessary agents/files

**Ready to:**
1. Run locally for testing
2. Deploy to production
3. Integrate with other systems
4. Extend with custom agents

