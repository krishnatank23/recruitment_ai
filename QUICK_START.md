# 🚀 QUICK START - JD Generation System

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd recruitment_ai
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create `.env` file:
```env
GROQ_API_KEY=your_groq_key_here
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_JSON=path/to/credentials.json
```

### Step 3: Start Backend
```bash
python -m uvicorn app.main:app --reload --port 8000
```
✅ Backend running at: **http://localhost:8000**

### Step 4: Start Frontend (New Terminal)
```bash
streamlit run ui/recruiter_portal_clean.py
```
✅ Frontend running at: **http://localhost:8501**

---

## 📋 6-Step Workflow

### Step 1: Select Role
- Pick a role from Google Sheet
- Automatically loads role data

### Step 2: Clarify Role
- Answer 5 multiple-choice questions (MCQ)
- LLM-generated based on role context

### Step 3: Build Profile
- LLM generates 15-field Ideal Candidate Profile:
  - Executive summary
  - Experience level
  - Must-have skills
  - Nice-to-have skills
  - Key responsibilities
  - Success metrics
  - Team fit
  - Work environment
  - Personality profile
  - Dealbreakers
  - Ideal candidate portrait
  - ...and more

### Step 4: Draft JD
- LLM generates professional Job Description:
  - About Us
  - Role Overview
  - Key Responsibilities (max 1.5 lines each)
  - Requirements (Must-have & Nice-to-have)
  - Who Will Succeed

### Step 5: Refine JD
- Chat-based refinement loop
- Give instructions like:
  - "Make it more senior"
  - "Add remote work flexibility"
  - "Focus on backend skills"
  - "Make it shorter and concise"
- LLM applies refinements

### Step 6: Export
- Download as **DOCX** or **PDF**
- Ready to share with hiring team

---

## 🔌 API Endpoints

### 1. **POST /jd/clarify**
Generate 5 clarifying MCQ questions.

**Request:**
```json
{
  "form_data": {
    "role": "Senior Software Engineer",
    "department": "Engineering"
  }
}
```

**Response:**
```json
{
  "success": true,
  "questions": [
    {
      "question": "What's the primary focus?",
      "options": ["Backend", "Frontend", "Full-stack", "DevOps"]
    }
  ]
}
```

---

### 2. **POST /jd/profile**
Build ideal candidate profile.

**Request:**
```json
{
  "form_data": {...},
  "answers": [
    {"question": "Q1", "answer": "Answer1"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "profile": {
    "role": "...",
    "executive_summary": "...",
    "must_have": [...],
    "nice_to_have": [...],
    ...
  }
}
```

---

### 3. **POST /jd/generate**
Generate job description.

**Request:**
```json
{
  "form_data": {...},
  "profile": {...}
}
```

**Response:**
```json
{
  "success": true,
  "jd": "# Senior Software Engineer\n\n## About Us\n..."
}
```

---

### 4. **POST /jd/refine**
Refine JD based on instruction.

**Request:**
```json
{
  "jd": "existing JD...",
  "instruction": "Make it shorter and add remote flexibility",
  "role": "Senior Software Engineer"
}
```

**Response:**
```json
{
  "success": true,
  "jd": "refined JD..."
}
```

---

### 5. **POST /pipeline/run_pipeline**
Full pipeline orchestration (all steps at once).

**Request:**
```json
{
  "form_data": {...},
  "clarification_answers": [...],
  "profile": null
}
```

**Response:**
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

## 🧪 Quick Test

### Test Backend Health
```bash
curl http://localhost:8000
```

Expected:
```json
{"status": "running", "service": "JD Generation API", "version": "1.0"}
```

### Test Clarify Endpoint
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

## 📊 File Structure

**Essential Files (Keep):**
```
app/
├── agents/
│   ├── jd_clarifier.py          ✅
│   ├── profile_builder.py        ✅
│   ├── jd_generator.py           ✅
│   └── jd_chatbot.py             ✅
├── api/
│   ├── jd.py                     ✅
│   └── pipeline.py               ✅ (updated)
└── utils/
    ├── llm.py                    ✅
    ├── file_export.py            ✅
    ├── google_form_loader.py     ✅
    ├── text_cleanup.py           ✅
    └── constants.py              ✅

ui/
├── streamlit_app.py              ✅
└── recruiter_portal_clean.py     ✅ (new)
```

**Files to Delete (if present):**
```
❌ agents/resume_parser.py
❌ agents/persona_builder.py
❌ agents/candidate_intel.py
❌ agents/evaluator.py
❌ agents/matcher.py
❌ agents/[others]
❌ api/candidates.py
❌ api/outreach.py
❌ ui/candidate_portal.py
❌ ui/recruiter_portal.py (old version)
❌ db/
❌ graphs/
```

---

## 🔍 Debugging

### View Backend Logs
```bash
# In backend terminal - watch for errors
grep "ERROR" output.log
grep "\[JD_" output.log
```

### Common Issues

#### 1. GROQ API Key Error
```
Error: Could not authenticate with Groq API
```
→ Check `GROQ_API_KEY` in `.env` file

#### 2. Google Sheet Not Loading
```
Error loading roles: Failed to authenticate with Google
```
→ Check `GOOGLE_CREDENTIALS_JSON` path in `.env`

#### 3. LLM Timeout
```
Error generating questions: timeout
```
→ Increase timeout or check Groq API status

#### 4. Export Failed
```
Error exporting to DOCX: Module not found
```
→ Run `pip install -r requirements.txt` again

---

## 📝 Code Changes Summary

### ✅ **app/main.py** - UPDATED
- Clean FastAPI app setup
- Improved health check response
- Clear router prefixes

### ✅ **app/api/pipeline.py** - UPDATED
- Removed old graph-based pipeline
- New 3-step clean pipeline:
  1. Build profile
  2. Generate JD
  3. Export to DOCX
- Enhanced error handling with logging
- Removed candidate matching logic

### ✅ **ui/recruiter_portal_clean.py** - NEW
- 6-step Streamlit workflow
- Clean session state management
- Proper error handling
- Progress bar visualization
- Export buttons for DOCX/PDF

### ✅ **app/api/jd.py** - NO CHANGES
- Already clean with 4 endpoints
- Works as-is

### ✅ **4 Core Agents** - NO CHANGES
- jd_clarifier.py
- profile_builder.py
- jd_generator.py
- jd_chatbot.py

---

## 🎯 Next Steps

1. **Test Locally**
   - Run backend + frontend
   - Go through 6-step workflow
   - Export JD as DOCX/PDF

2. **Deploy to Production**
   - Use Docker or cloud platform
   - Set environment variables
   - Configure CORS for frontend

3. **Integrate with Other Systems**
   - Use `/pipeline/run_pipeline` for programmatic access
   - Call individual endpoints for custom workflows
   - Add authentication/authorization

4. **Extend with Custom Agents**
   - Add new refinement agents
   - Customize prompts in `agents/`
   - Add new export formats

---

## 📞 Support

Check terminal logs for detailed error messages. All backend logs include `[COMPONENT]` prefix:
- `[JD_PIPELINE]` - Pipeline orchestration
- `[PROFILE_BUILDER]` - Profile generation
- `[JD_GENERATOR]` - JD generation

**Resources:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [LangChain Docs](https://python.langchain.com/)
- [Groq API Docs](https://console.groq.com/)

---

## ✨ You're Ready!

Your clean JD generation system is ready to use. Start with the 5-minute setup above and you'll have a professional JD generation workflow running in minutes. 🎉

