# 👥 CANDIDATE MATCHING - QUICK START

## ⚡ 1-Minute Setup

### Start Backend
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Start Frontend
```bash
streamlit run ui/streamlit_app.py
```

### Open UI
```
http://localhost:8501
→ Click "Match Candidates"
```

---

## 🎯 The 3-Step Workflow

### Step 1: Upload Resumes
- Select files: PDF, DOCX, TXT, or ZIP
- Click "Parse Resumes"
- System extracts text from all files

### Step 2: Create Personas
- Paste job description/profile
- Click "Generate 5 Personas"
- LLM creates 5 distinct candidate personas

### Step 3: View Matching Results
- See match scores for each candidate vs each persona
- View reasoning, strengths, and gaps
- Download results as JSON

---

## 📊 What You See

For each candidate, a matrix showing:
```
Candidate Name:
┌─────────────────────┬────────────┐
│ Persona Name        │ Match %    │
├─────────────────────┼────────────┤
│ Senior Technical    │ 85% ✅     │
│ Backend Architect   │ 78% 🟡     │
│ Full-Stack Engineer │ 65% 🟡     │
│ DevOps Engineer     │ 45% 🔴     │
│ Team Lead           │ 72% 🟡     │
└─────────────────────┴────────────┘
```

Click "See details" for reasoning, strengths, and gaps.

---

## 🆕 New Files Created

| File | Purpose |
|------|---------|
| `app/agents/persona_builder.py` | Generate personas from job profile |
| `app/agents/resume_parser.py` | Parse uploaded resumes |
| `app/agents/candidate_matcher.py` | Match resumes to personas (LLM scoring) |
| `app/api/candidate_matching.py` | Backend API endpoints |
| `ui/candidate_matching_portal.py` | 3-step Streamlit UI |

---

## 🔗 API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /candidate_matching/generate_personas` | Create personas from profile |
| `POST /candidate_matching/parse_resumes` | Extract text from resume files |
| `POST /candidate_matching/match_candidates` | Score candidates vs personas |
| `POST /candidate_matching/run_full_match` | All 3 steps in one call |

---

## 📝 Example API Call

```bash
# Full pipeline: Upload, generate personas, match
curl -X POST http://localhost:8000/candidate_matching/run_full_match \
  -F 'job_profile=Senior Backend Engineer with 5+ years...' \
  -F 'resumes=@resume1.pdf' \
  -F 'resumes=@resume2.pdf'
```

Response:
```json
{
  "success": true,
  "personas": [...],
  "matches": [
    {
      "candidate_name": "John Doe",
      "persona_matches": [
        {
          "persona_name": "Senior Technical Lead",
          "match_score": 85,
          "match_percentage": "85%",
          "verdict": "Strong Match",
          "reasoning": "Strong architecture background..."
        }
      ]
    }
  ]
}
```

---

## ✅ Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 8501
- [ ] Visit http://localhost:8501
- [ ] Click "Match Candidates"
- [ ] Upload test resumes
- [ ] Enter job profile
- [ ] Generate personas
- [ ] View matching results
- [ ] Download JSON export

---

## 🎯 Key Features

✨ **3 LLM-Powered Agents:**
1. **Persona Builder** - Creates 5 distinct candidate personas from job profile
2. **Resume Parser** - Extracts text from PDF, DOCX, TXT, ZIP files
3. **Candidate Matcher** - Scores each resume against each persona (0-100%)

🎨 **Color-Coded Scores:**
- 🟢 80%+ = Strong Match
- 🟡 60-79% = Good/Moderate Match
- 🔴 <60% = Weak Match

📊 **Detailed Analysis:**
- Match percentage
- Verdict (Strong/Good/Moderate/Weak/No Match)
- Reasoning (why this score)
- Key strengths match
- Experience/skill gaps

💾 **Export Results:**
- Download as JSON
- Share with team
- Integrate with ATS

---

## 🐛 Troubleshooting

**Resume not parsing?**
→ Check file format is supported (PDF, DOCX, TXT, ZIP)

**No personas generated?**
→ Job profile too short - use 2-3 sentences minimum

**Match scores seem low?**
→ Check if skills match between profile and resumes

**API timing out?**
→ Process fewer resumes (max 10-15 per batch)

---

## 📖 Full Documentation

See `CANDIDATE_MATCHING_GUIDE.md` for:
- Complete API reference
- Persona structure
- Match scoring logic
- Advanced configuration
- Use cases & examples

---

## 🚀 You're Ready!

Everything is set up. Just run the backend + frontend and start matching candidates! 🎉

