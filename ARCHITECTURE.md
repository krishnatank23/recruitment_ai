# 📐 System Architecture & Reference

## High-Level Data Flow

```
┌───────────────────────────────────────────────────────────────┐
│                    RECRUITER (User)                           │
│                  Opens Browser                                │
└───────────────────┬───────────────────────────────────────────┘
                    │
                    ↓ http://localhost:8501
┌───────────────────────────────────────────────────────────────┐
│          STREAMLIT FRONTEND (recruiter_portal_clean.py)       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Step 1: Select Role                                     │ │
│  │ └─────────────────────────────────────────────────────┐ │ │
│  │   Fetches: Google Sheet                               │ │ │
│  │   GET /jd/... (not directly)                          │ │ │
│  │   Returns: List of roles                              │ │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Step 2: Clarify Role (5 MCQ)                            │ │
│  │ └─────────────────────────────────────────────────────┐ │ │
│  │   Calls: POST /jd/clarify {form_data}                 │ │ │
│  │   LLM: Generates 5 questions                           │ │ │
│  │   Returns: [{question, options}]                       │ │ │
│  │   User: Selects answers                               │ │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Step 3: Build Profile (LLM-generated)                  │ │
│  │ └─────────────────────────────────────────────────────┐ │ │
│  │   Calls: POST /jd/profile {form_data, answers}        │ │ │
│  │   LLM: Builds 15-field profile                        │ │ │
│  │   Returns: {role, executive_summary, ...15 fields}    │ │ │
│  │   Displays: Rendered HTML profile                     │ │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Step 4: Draft JD (LLM-generated)                        │ │
│  │ └─────────────────────────────────────────────────────┐ │ │
│  │   Calls: POST /jd/generate {form_data, profile}       │ │ │
│  │   LLM: Generates markdown JD                          │ │ │
│  │   Returns: Markdown JD text                           │ │ │
│  │   Displays: Formatted HTML JD                         │ │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Step 5: Refine JD (Chat loop)                           │ │
│  │ └─────────────────────────────────────────────────────┐ │ │
│  │   User enters: "Make it shorter"                      │ │ │
│  │   Calls: POST /jd/refine {jd, instruction}            │ │ │
│  │   LLM: Applies refinement                             │ │ │
│  │   Returns: Refined JD                                 │ │ │
│  │   Loop: Users can refine multiple times               │ │ │
│  │         (No step regression - maintains final)         │ │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Step 6: Export                                          │ │
│  │ └─────────────────────────────────────────────────────┐ │ │
│  │   Button: Download as DOCX                            │ │ │
│  │   Function: export_to_docx(jd)                        │ │ │
│  │   Output: /exports/RoleName_TIMESTAMP.docx            │ │ │
│  │   Browser: Download file                              │ │ │
│  │   ───────────────────────                             │ │ │
│  │   Button: Download as PDF                             │ │ │
│  │   Function: export_to_pdf(jd)                         │ │ │
│  │   Output: /exports/RoleName_TIMESTAMP.pdf             │ │ │
│  │   Browser: Download file                              │ │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────┬───────────────────────────────────────────┘
                    │
                    │ HTTP API Calls
                    ↓ http://localhost:8000
┌───────────────────────────────────────────────────────────────┐
│         FASTAPI BACKEND (app/main.py)                         │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Router: app/api/jd.py                               │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ POST /jd/clarify                                    │   │
│  │ POST /jd/profile                                    │   │
│  │ POST /jd/generate                                   │   │
│  │ POST /jd/refine                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Router: app/api/pipeline.py                          │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ POST /pipeline/run_pipeline                          │   │
│  │ └─ Orchestrates all 3 steps at once                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────┬───────────────────────────────────────────┘
                    │
                    ↓ Python function calls
┌───────────────────────────────────────────────────────────────┐
│           LLM AGENTS (app/agents/)                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  jd_clarifier.py                                            │
│  ├─ generate_clarifying_questions(form_data)               │
│  ├─ LLM Prompt: Generate 5 MCQ questions                   │
│  └─ Returns: List of {question, options}                   │
│                                                               │
│  profile_builder.py                                         │
│  ├─ build_profile(form_data, clarification_answers)        │
│  ├─ LLM Prompt: Build 15-field profile                     │
│  ├─ Parse JSON response                                    │
│  └─ Returns: {15 fields of ideal candidate}                │
│                                                               │
│  jd_generator.py                                            │
│  ├─ generate_jd(form_data, profile)                        │
│  ├─ LLM Prompt: Generate markdown JD                       │
│  ├─ Constraint: Key responsibilities = 1-1.5 lines         │
│  └─ Returns: Markdown formatted JD                         │
│                                                               │
│  jd_chatbot.py                                              │
│  ├─ refine_jd(current_jd, instruction, role)               │
│  ├─ LLM Prompt: Refine JD based on instruction             │
│  └─ Returns: Refined JD text                               │
│                                                               │
└───────────────────┬───────────────────────────────────────────┘
                    │
                    ↓ LLM API calls
┌───────────────────────────────────────────────────────────────┐
│              GROQ API (LLM Provider)                          │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Uses: langchain_groq.ChatGroq                              │
│  Model: mixtral-8x7b (or other)                             │
│  Auth: GROQ_API_KEY from .env                               │
│                                                               │
│  Characteristics:                                            │
│  • Fast inference (~1-2 seconds per call)                    │
│  • Token-efficient                                           │
│  • Good for structured generation (JSON)                     │
│  • Requires authentication                                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## API Endpoint Reference

### 1️⃣ `/jd/clarify` - Generate Questions

```
POST /jd/clarify
Content-Type: application/json

Request:
{
  "form_data": {
    "role": "Senior Software Engineer",
    "department": "Engineering",
    "location": "New York",
    ...
  }
}

Response (200 OK):
{
  "success": true,
  "questions": [
    {
      "question": "What's the primary focus of this role?",
      "options": ["Backend", "Frontend", "Full-stack", "DevOps"]
    },
    {
      "question": "Experience level?",
      "options": ["Entry", "Mid", "Senior", "Principal"]
    },
    ...
  ]
}

Response (4xx/5xx):
{
  "success": false,
  "error": "Error message",
  "questions": []
}
```

---

### 2️⃣ `/jd/profile` - Build Profile

```
POST /jd/profile
Content-Type: application/json

Request:
{
  "form_data": {...},
  "answers": [
    {"question": "What's the primary focus?", "answer": "Backend"},
    {"question": "Experience level?", "answer": "Senior"},
    ...
  ]
}

Response (200 OK):
{
  "success": true,
  "profile": {
    "role": "Senior Software Engineer",
    "department": "Engineering",
    "executive_summary": "...",
    "experience": "5-7 years in backend...",
    "must_have": ["Python", "PostgreSQL", "AWS", ...],
    "nice_to_have": ["Kubernetes", "Rust", ...],
    "key_responsibilities": ["Design scalable systems", ...],
    "success_metrics": ["Ship features on time", ...],
    "team_fit": "...",
    "work_environment": "...",
    "personality_profile": "...",
    "dealbreakers": [...],
    "ideal_candidate_portrait": "...",
    ...
  }
}

Response (4xx/5xx):
{
  "success": false,
  "error": "Error building profile",
  "profile": {}
}
```

---

### 3️⃣ `/jd/generate` - Generate JD

```
POST /jd/generate
Content-Type: application/json

Request:
{
  "form_data": {...},
  "profile": {...}  (from /jd/profile)
}

Response (200 OK):
{
  "success": true,
  "jd": "# Senior Software Engineer\n\n## About Us\n[company info]\n\n## Role Overview\n[overview]\n\n## Key Responsibilities\n- [resp 1]\n- [resp 2]\n\n## Requirements\n### Must Have\n- Python\n- PostgreSQL\n...\n"
}

Response (4xx/5xx):
{
  "success": false,
  "error": "Error generating JD",
  "jd": ""
}
```

---

### 4️⃣ `/jd/refine` - Refine JD

```
POST /jd/refine
Content-Type: application/json

Request:
{
  "jd": "# Senior Software Engineer\n...",
  "instruction": "Make it shorter and emphasize remote work",
  "role": "Senior Software Engineer",
  "session_id": "recruiter_session"
}

Response (200 OK):
{
  "success": true,
  "jd": "[refined JD with instruction applied]"
}

Response (4xx/5xx):
{
  "success": false,
  "error": "Error refining JD",
  "jd": "[original JD]"
}
```

---

### 5️⃣ `/pipeline/run_pipeline` - Full Orchestration

```
POST /pipeline/run_pipeline
Content-Type: application/json

Request:
{
  "form_data": {...},
  "clarification_answers": [...],
  "profile": null  (optional - can pass pre-built profile)
}

Response (200 OK):
{
  "success": true,
  "message": "JD generation complete",
  "jd": "# Senior Software Engineer\n...",
  "export_path": "/exports/Senior_Software_Engineer_20240211_120530.docx",
  "profile": {...}
}

Response (4xx/5xx):
{
  "success": false,
  "message": "Pipeline failed: Error message",
  "error": "Detailed error",
  "jd": "",
  "export_path": null,
  "profile": {}
}
```

---

## Session State Management (Frontend)

```python
# Streamlit Session State Tracking

st.session_state.step                    # Current step (1-6)
st.session_state.form_data               # Role data from Google Sheet
st.session_state.questions               # Generated 5 MCQ questions
st.session_state.clarification_answers   # User answers to questions
st.session_state.profile                 # Generated profile
st.session_state.jd                      # Current JD (gets updated on refine)
st.session_state.jd_history              # JD versions history
st.session_state.refinement_messages     # Chat message history for Step 5
```

---

## Error Handling Strategy

### Backend Error Responses

```python
# Each endpoint returns:
# - success: bool (indicates success/failure)
# - Relevant data fields (questions, profile, jd, etc.)
# - error: str (if success=false)
# - message: str (additional context)

# Logging format: [COMPONENT] Step X: Description
# Helps with debugging by searching logs

# Example log output:
# [JD_PIPELINE] Step 1: Building ideal candidate profile...
# [JD_PIPELINE] Step 1: Profile built successfully
# [JD_PIPELINE] Profile keys: ['role', 'executive_summary', ...]
# [JD_PIPELINE] Step 2: Generating JD from profile...
# [JD_PIPELINE] Step 2: JD generated successfully
# [JD_PIPELINE] Step 3: Exporting JD to DOCX...
# [JD_PIPELINE] Step 3: Exported to /exports/...
# [JD_PIPELINE] Pipeline complete! ✓
```

### Frontend Error Handling

```python
# User-facing error messages

if response.success:
    # Display result
    st.success("✓ Step completed")
else:
    # Display error with context
    st.error(f"Error in Step X: {response.error}")
    # Provide retry option
```

---

## LLM Prompt Structure

### Pattern Used in All Agents

```
[SYSTEM CONTEXT]
You are a [role] AI. Your task is to [task].

[INPUT DATA]
- Role: {role}
- Department: {department}
- Experience: {experience}
...

[INSTRUCTIONS]
1. Generate [what to generate]
2. Format as [format]
3. Constraints: [constraints]

[OUTPUT FORMAT]
```json
{
  "field1": "value1",
  "field2": "value2",
  ...
}
```

[EXAMPLES]
[Optional examples if needed]
```

---

## Deployment Checklist

- [ ] Backend can start: `python -m uvicorn app.main:app --reload`
- [ ] Frontend can start: `streamlit run ui/recruiter_portal_clean.py`
- [ ] `.env` file configured with:
  - [ ] GROQ_API_KEY
  - [ ] GOOGLE_SHEET_ID
  - [ ] GOOGLE_CREDENTIALS_JSON
- [ ] Google Sheet accessible and contains roles
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Backend responds to health check: `GET /`
- [ ] Full 6-step workflow completes without errors
- [ ] Export to DOCX works
- [ ] Export to PDF works
- [ ] Logs available and readable (check backend terminal)

---

## Performance Metrics

**Typical latencies per step:**
- Step 1 (Select Role): ~100ms (local)
- Step 2 (Clarify): 3-5s (LLM call)
- Step 3 (Build Profile): 5-8s (LLM call)
- Step 4 (Draft JD): 3-5s (LLM call)
- Step 5 (Refine): 3-5s per refinement (LLM call)
- Step 6 (Export): 1-2s (file generation)

**Total time for complete workflow: ~20-30 seconds**

---

## Troubleshooting Matrix

| Problem | Cause | Solution |
|---------|-------|----------|
| Backend won't start | Port 8000 in use | Use different port: `--port 8001` |
| GROQ API error | Invalid API key | Check `.env` GROQ_API_KEY |
| Google Sheet not loading | Auth failed | Verify GOOGLE_CREDENTIALS_JSON path |
| LLM returns empty | Model timeout | Check Groq API status |
| Export fails | Missing python-docx | Run `pip install python-docx` |
| UI stuck on Step X | Session state issue | Refresh browser |
| Logs not showing | Missing [COMPONENT] prefix | Check backend terminal directly |

