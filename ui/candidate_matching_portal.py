"""
Candidate Matching Portal - 3-Step Workflow
Step 1: Upload Resumes (ZIP/PDF/DOCX)
Step 2: Create Personas from Job Profile (LLM)
Step 3: Match Candidates to Personas (LLM Scoring)
"""

import streamlit as st
import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Path setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.agents.resume_parser import parse_candidate_resumes
from app.agents.persona_builder import generate_personas
from app.agents.candidate_matcher import match_candidates_to_personas, get_best_matches

# ════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════

API_BASE_URL = "http://localhost:8000"

# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def render_step_progress(current_step: int):
    """Render 3-step progress bar."""
    progress = current_step / 3
    steps = ["Upload Resumes", "Create Personas", "Match & Score"]
    st.progress(progress, text=f"Step {current_step}/3: {steps[current_step-1]}")

def render_persona_card(persona: dict):
    """Render a persona as a card."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    ">
        <h3 style="margin-top: 0;">{persona.get('name', 'Unknown')}</h3>
        <p><b>Background:</b> {persona.get('background', 'N/A')}</p>
        <p><b>Experience:</b> {persona.get('experience_level', 'N/A')}</p>
        <p><b>Key Strengths:</b> {', '.join(persona.get('key_strengths', []))}</p>
        <p><b>Must-Have Skills:</b> {', '.join(persona.get('must_have_skills', []))}</p>
        <p><b>Ideal For:</b> {persona.get('ideal_for', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

def _average_persona_score(match_scores: list) -> float:
    """Return final percentage as average of up to 5 persona scores."""
    if not match_scores:
        return 0.0

    top_five = match_scores[:5]
    numeric_scores = []
    for match in top_five:
        score = match.get("match_score", 0)
        try:
            numeric_scores.append(float(score))
        except (TypeError, ValueError):
            numeric_scores.append(0.0)

    return sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0.0

def _match_percentage_explanation(avg_score: float) -> str:
    """Short explanation for the final average match percentage."""
    if avg_score >= 85:
        return "Excellent fit: profile aligns strongly across most personas."
    if avg_score >= 70:
        return "Good fit: strong alignment with minor gaps to evaluate."
    if avg_score >= 55:
        return "Moderate fit: potential candidate, but key gaps need validation."
    return "Low fit: significant gaps against persona expectations."

def _build_overall_rows(matches: list) -> list:
    """Build candidate-level overall score rows for UI display."""
    rows = []
    for candidate in matches:
        candidate_name = candidate.get("candidate_name", "Unknown")
        persona_matches = candidate.get("persona_matches", [])
        overall_score = _average_persona_score(persona_matches)
        rows.append({
            "candidate_name": candidate_name,
            "overall_score": overall_score,
            "overall_percentage": f"{round(overall_score)}%",
            "explanation": _match_percentage_explanation(overall_score),
        })
    return sorted(rows, key=lambda x: x["overall_score"], reverse=True)

def render_match_result(candidate_name: str, match_scores: list):
    """Render matching results for a candidate."""
    st.markdown(f"### {candidate_name}")

    if not match_scores:
        st.warning("No persona scores available for this candidate.")
        return

    final_avg = _average_persona_score(match_scores)
    final_percentage = f"{round(final_avg)}%"
    explanation = _match_percentage_explanation(final_avg)

    st.markdown(
        f"""
        <div style="
            background: #ecfeff;
            border: 1px solid #a5f3fc;
            padding: 12px 14px;
            border-radius: 8px;
            margin: 8px 0 14px 0;
        ">
            <div style="font-size: 14px; color: #0f172a;">
                <b>Final Match Percentage (Avg of 5 Personas):</b> {final_percentage}
            </div>
            <div style="font-size: 13px; color: #334155; margin-top: 4px;">
                {explanation}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create columns for each persona
    cols = st.columns(len(match_scores))
    
    for col, match in zip(cols, match_scores):
        with col:
            score = match.get("match_score", 0)
            
            # Color based on score
            if score >= 80:
                color = "🟢"
            elif score >= 60:
                color = "🟡"
            else:
                color = "🔴"
            
            st.markdown(f"""
            <div style="
                background: #f0f2f6;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            ">
                <h4>{match.get('persona_name', 'Unknown')}</h4>
                <h2 style="margin: 10px 0; color: #0066cc;">
                    {color} {match.get('match_percentage', '0%')}
                </h2>
                <p style="font-size: 12px; color: #555;">
                    <b>{match.get('verdict', 'Unknown')}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show details in expander
            with st.expander(f"See details"):
                st.write(f"**Score:** {match.get('match_score', 0)}/100")
                st.write(f"**Verdict:** {match.get('verdict', 'Unknown')}")
                st.write(f"**Reasoning:** {match.get('reasoning', 'N/A')}")
                
                if match.get('key_strengths_match'):
                    st.write(f"**Strengths:** {', '.join(match.get('key_strengths_match', []))}")
                
                if match.get('gaps'):
                    st.write(f"**Gaps:** {', '.join(match.get('gaps', []))}")

# ════════════════════════════════════════════════════════════
# STEP 1: UPLOAD RESUMES
# ════════════════════════════════════════════════════════════

def render_upload_resumes():
    """Step 1: Upload candidate resumes."""
    st.markdown("### Step 1: Upload Candidate Resumes")
    
    st.info("📤 Upload resumes in ZIP, PDF, DOCX, or TXT format")
    
    uploaded_files = st.file_uploader(
        "Select resume files:",
        type=["pdf", "docx", "txt", "zip", "doc"],
        accept_multiple_files=True,
        key="resume_uploader"
    )
    
    if uploaded_files:
        st.success(f"✓ {len(uploaded_files)} file(s) selected")
        
        # Save and parse resumes
        if st.button("📥 Parse Resumes", key="parse_button"):
            with st.spinner("Parsing resumes..."):
                try:
                    import tempfile
                    
                    temp_dir = tempfile.mkdtemp()
                    temp_paths = []
                    
                    # Save files
                    for uploaded_file in uploaded_files:
                        temp_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        temp_paths.append(temp_path)
                    
                    # Parse resumes
                    result = parse_candidate_resumes(temp_paths)
                    
                    if result.get("success"):
                        st.session_state.step = 2
                        st.session_state.candidates = result.get("candidates", [])
                        st.success(f"✓ Parsed {result.get('total', 0)} resumes successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Error parsing resumes: {str(e)}")
    
    else:
        st.warning("No files selected")

# ════════════════════════════════════════════════════════════
# STEP 2: CREATE PERSONAS
# ════════════════════════════════════════════════════════════

def render_create_personas():
    """Step 2: Create personas from job profile."""
    st.markdown("### Step 2: Create Personas from Job Profile")
    
    st.info("📝 Paste or enter the job profile/description to generate 5 personas")
    
    job_profile = st.text_area(
        "Job Profile/Description:",
        height=150,
        placeholder="Senior Software Engineer - 5+ years experience in backend development...",
        key="job_profile"
    )
    
    if st.button("✨ Generate 5 Personas", key="generate_personas_button"):
        if not job_profile.strip():
            st.error("Please enter a job profile first")
            return
        
        with st.spinner("Generating personas..."):
            try:
                result = generate_personas(job_profile)
                
                if result.get("success"):
                    st.session_state.personas = result.get("personas", [])
                    st.session_state.persona_source_profile = job_profile.strip()
                    st.session_state.step = 3
                    st.success(f"✓ Generated {result.get('count', 0)} personas!")
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Error generating personas: {str(e)}")
    
    # Show uploaded candidates so far
    if "candidates" in st.session_state and st.session_state.candidates:
        st.markdown(f"**Candidates Uploaded:** {len(st.session_state.candidates)}")
        for cand in st.session_state.candidates:
            st.write(f"• {cand.get('name', 'Unknown')}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Upload", key="step2_back"):
            st.session_state.step = 1
            st.rerun()

# ════════════════════════════════════════════════════════════
# STEP 3: MATCH & SCORE
# ════════════════════════════════════════════════════════════

def render_match_candidates():
    """Step 3: Match candidates to personas and show scores."""
    st.markdown("### Step 3: Candidate Matching Results")
    
    st.info("🎯 Matching candidates to personas and generating match scores...")
    
    # Show personas first
    st.markdown("#### Generated Personas:")
    source_profile = st.session_state.get("persona_source_profile", "").strip()
    if source_profile:
        st.caption("Personas generated from this job profile:")
        with st.expander("View full job profile text", expanded=True):
            st.text_area(
                "Job profile used for persona generation",
                value=source_profile,
                height=220,
                disabled=True,
                label_visibility="collapsed",
            )
    
    for persona in st.session_state.get("personas", []):
        render_persona_card(persona)
    
    st.markdown("---")
    st.markdown("#### Candidate Matching Scores:")
    
    # Run matching
    if "match_results" not in st.session_state:
        with st.spinner("Matching candidates to personas..."):
            try:
                candidates = st.session_state.get("candidates", [])
                personas = st.session_state.get("personas", [])
                
                if not candidates:
                    st.error("No candidates to match")
                    return
                
                if not personas:
                    st.error("No personas to match against")
                    return
                
                # Perform matching
                match_results = match_candidates_to_personas(candidates, personas)
                
                if match_results.get("success"):
                    st.session_state.match_results = match_results
                else:
                    st.error(f"Error: {match_results.get('error', 'Unknown error')}")
                    return
                    
            except Exception as e:
                st.error(f"Error during matching: {str(e)}")
                return
    
    # Display results
    match_results = st.session_state.get("match_results", {})
    matches = match_results.get("matches", [])

    st.markdown("#### Overall Match % (Average of 5 Personas)")
    overall_rows = _build_overall_rows(matches)
    if overall_rows:
        for idx, row in enumerate(overall_rows, start=1):
            st.markdown(
                f"""
                <div style="
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 10px 12px;
                    margin-bottom: 8px;
                ">
                    <div style="font-size:14px; color:#0f172a;">
                        <b>#{idx} {row['candidate_name']}</b> - <b>{row['overall_percentage']}</b>
                    </div>
                    <div style="font-size:12px; color:#475569; margin-top: 2px;">
                        {row['explanation']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No candidate-level overall score available yet.")

    st.markdown("---")
    
    for candidate in matches:
        render_match_result(
            candidate.get("candidate_name", "Unknown"),
            candidate.get("persona_matches", [])
        )
    
    st.markdown("---")
    
    # Summary section
    st.markdown("#### Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Candidates", len(st.session_state.get("candidates", [])))
    with col2:
        st.metric("Total Personas", len(st.session_state.get("personas", [])))
    with col3:
        st.metric("Total Evaluations", 
                 len(st.session_state.get("candidates", [])) * len(st.session_state.get("personas", [])))
    
    # Export results
    st.markdown("#### Export Results")
    
    if st.button("📥 Download Results as JSON"):
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "personas": st.session_state.get("personas", []),
            "matching_results": st.session_state.get("match_results", {}),
            "total_candidates": len(st.session_state.get("candidates", [])),
            "total_personas": len(st.session_state.get("personas", []))
        }
        
        st.download_button(
            label="Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"candidate_matching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="step3_back"):
            st.session_state.step = 2
            st.rerun()
    
    with col2:
        if st.button("🔄 Start Over", key="step3_restart"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.step = 1
            st.rerun()

# ════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════

def main():
    """Main candidate matching portal application."""
    st.set_page_config(
        page_title="Candidate Matching",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = 1
    
    # Header
    st.title("👥 Candidate Matching Portal")
    st.markdown("Match candidates to job-specific personas using AI scoring")
    
    # Progress bar
    render_step_progress(st.session_state.step)
    
    st.markdown("---")
    
    # Route to appropriate step
    if st.session_state.step == 1:
        render_upload_resumes()
    elif st.session_state.step == 2:
        render_create_personas()
    elif st.session_state.step == 3:
        render_match_candidates()

if __name__ == "__main__":
    main()
