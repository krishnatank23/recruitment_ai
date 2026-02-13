"""
Recruiter Portal - Clean JD Generation UI (Minimal Setup)
6-Step Workflow: Select Role → Clarify → Profile → Draft JD → Refine → Export
"""

import streamlit as st
import sys
import os
import json
import markdown
from datetime import datetime

# Path setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports
from app.agents.jd_clarifier import generate_clarifying_questions
from app.agents.profile_builder import build_profile
from app.agents.jd_generator import generate_jd
from app.agents.jd_chatbot import refine_jd
from app.utils.google_form_loader import fetch_google_form_data
from app.utils.file_export import export_to_docx, export_to_pdf

# ════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════

STEP_LABELS = {
    1: "Select Role",
    2: "Clarify Role",
    3: "Build Profile",
    4: "Draft JD",
    5: "Refine JD",
    6: "Export",
}

# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def render_jd_html(jd_text: str):
    """Render JD markdown as styled HTML."""
    html_body = markdown.markdown(jd_text, extensions=["extra"])
    st.markdown(
        f"""
        <div style="
            font-family: 'Inter', sans-serif;
            max-width: 860px; margin: 0 auto;
            background: white; padding: 32px 36px;
            border-radius: 14px; line-height: 1.7;
            color: #1E293B; border: 1px solid #E2E8F0;
        ">{html_body}</div>
        """,
        unsafe_allow_html=True
    )

def render_profile_html(profile: dict):
    """Render ideal candidate profile as styled HTML."""
    html = "<div style='font-family: Inter; color: #1E293B; line-height: 1.7;'>"
    for key, value in profile.items():
        if isinstance(value, list):
            html += f"<p><b>{key.replace('_', ' ').title()}:</b><br/>"
            for item in value:
                html += f"• {item}<br/>"
            html += "</p>"
        else:
            html += f"<p><b>{key.replace('_', ' ').title()}:</b> {value}</p>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_step_progress(current_step: int):
    """Render 6-step progress bar."""
    progress = current_step / 6
    st.progress(progress, text=f"Step {current_step}/6: {STEP_LABELS[current_step]}")

# ════════════════════════════════════════════════════════════
# STEP 1: SELECT ROLE
# ════════════════════════════════════════════════════════════

def render_select_role():
    """Step 1: Fetch roles from Google Sheet and let recruiter select."""
    st.markdown("### Step 1: Select Role")
    
    try:
        roles = fetch_google_form_data()  # Returns list of role dicts
        role_names = [r.get("role", f"Role {i}") for i, r in enumerate(roles)]
        
        selected_idx = st.selectbox(
            "Select a role to generate JD for:",
            range(len(roles)),
            format_func=lambda i: role_names[i]
        )
        
        form_data = roles[selected_idx]
        
        if st.button("✓ Proceed to Clarification", key="step1_proceed"):
            st.session_state.step = 2
            st.session_state.form_data = form_data
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading roles: {str(e)}")

# ════════════════════════════════════════════════════════════
# STEP 2: CLARIFY ROLE (MCQ)
# ════════════════════════════════════════════════════════════

def render_clarify_role():
    """Step 2: Generate 5 clarifying questions and collect answers."""
    st.markdown("### Step 2: Clarify the Role")
    
    form_data = st.session_state.form_data
    
    if "questions" not in st.session_state:
        with st.spinner("Generating clarifying questions..."):
            try:
                questions = generate_clarifying_questions(form_data=form_data)
                if isinstance(questions, str):
                    questions = json.loads(questions)
                st.session_state.questions = questions
            except Exception as e:
                st.error(f"Error generating questions: {str(e)}")
                return
    
    questions = st.session_state.questions
    answers = []
    
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}: {q.get('question', '')}**")
        answer = st.radio(
            label=f"Answer to Q{i+1}",
            options=q.get('options', []),
            label_visibility="collapsed",
            key=f"q_{i}"
        )
        answers.append({
            "question": q.get("question"),
            "answer": answer
        })
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Role Selection", key="step2_back"):
            st.session_state.step = 1
            st.rerun()
    
    with col2:
        if st.button("✓ Build Profile →", key="step2_proceed"):
            st.session_state.step = 3
            st.session_state.clarification_answers = answers
            st.rerun()

# ════════════════════════════════════════════════════════════
# STEP 3: BUILD PROFILE
# ════════════════════════════════════════════════════════════

def render_profile_builder():
    """Step 3: Generate ideal candidate profile using LLM."""
    st.markdown("### Step 3: Build Ideal Candidate Profile")
    
    if "profile" not in st.session_state:
        with st.spinner("Building ideal candidate profile..."):
            try:
                profile = build_profile(
                    form_data=st.session_state.form_data,
                    clarification_answers=st.session_state.clarification_answers
                )
                st.session_state.profile = profile
            except Exception as e:
                st.error(f"Error building profile: {str(e)}")
                return
    
    profile = st.session_state.profile
    render_profile_html(profile)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Clarification", key="step3_back"):
            st.session_state.step = 2
            st.rerun()
    
    with col2:
        if st.button("✓ Generate JD →", key="step3_proceed"):
            st.session_state.step = 4
            st.rerun()

# ════════════════════════════════════════════════════════════
# STEP 4: DRAFT JD
# ════════════════════════════════════════════════════════════

def render_draft_jd():
    """Step 4: Generate Job Description from profile."""
    st.markdown("### Step 4: Draft Job Description")
    
    if "jd" not in st.session_state:
        with st.spinner("Generating Job Description..."):
            try:
                jd = generate_jd(
                    form_data=st.session_state.form_data,
                    profile=st.session_state.profile
                )
                st.session_state.jd = jd
            except Exception as e:
                st.error(f"Error generating JD: {str(e)}")
                return
    
    jd = st.session_state.jd
    render_jd_html(jd)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Profile", key="step4_back"):
            st.session_state.step = 3
            st.rerun()
    
    with col2:
        if st.button("✓ Refine JD →", key="step4_proceed"):
            st.session_state.step = 5
            st.session_state.jd_history = [jd]  # For refinement history
            st.rerun()

# ════════════════════════════════════════════════════════════
# STEP 5: REFINE JD (CHAT)
# ════════════════════════════════════════════════════════════

def render_refine_jd():
    """Step 5: Refine JD through chat-based refinement loop."""
    st.markdown("### Step 5: Refine Job Description")
    
    st.info("💡 Give instructions to refine the JD (e.g., 'Make it shorter', 'Add more seniority requirements')")
    
    # Chat history for refinement
    if "refinement_messages" not in st.session_state:
        st.session_state.refinement_messages = []
    
    # Display refinement history
    for msg in st.session_state.refinement_messages:
        if msg["role"] == "user":
            st.write(f"**You:** {msg['content']}")
        else:
            st.write(f"**AI:** {msg['content'][:200]}...")  # Preview
    
    # Input for refinement instruction
    instruction = st.text_input(
        "Enter refinement instruction:",
        placeholder="e.g., 'Make it more concise' or 'Add remote work flexibility'",
        key="refine_input"
    )
    
    if instruction:
        try:
            refined_jd = refine_jd(
                current_jd=st.session_state.jd,
                instruction=instruction,
                role=st.session_state.form_data.get("role", ""),
                session_id="recruiter_session"
            )
            
            st.session_state.jd = refined_jd
            st.session_state.refinement_messages.append({"role": "user", "content": instruction})
            st.session_state.refinement_messages.append({"role": "assistant", "content": refined_jd})
            
            st.success("✓ JD refined!")
            st.rerun()
        except Exception as e:
            st.error(f"Error refining JD: {str(e)}")
    
    st.markdown("---")
    st.markdown("**Current JD Version:**")
    render_jd_html(st.session_state.jd)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Back to Draft", key="step5_back"):
            st.session_state.step = 4
            st.rerun()
    
    with col3:
        if st.button("✓ Export JD →", key="step5_proceed"):
            st.session_state.step = 6
            st.rerun()

# ════════════════════════════════════════════════════════════
# STEP 6: EXPORT JD
# ════════════════════════════════════════════════════════════

def render_export():
    """Step 6: Export JD as DOCX or PDF."""
    st.markdown("### Step 6: Export Job Description")
    
    role = st.session_state.form_data.get("role", "JobDescription")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{role.replace(' ', '_')}_{timestamp}"
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export as DOCX"):
            try:
                docx_path = export_to_docx(st.session_state.jd, filename)
                st.success(f"✓ Exported to: {docx_path}")
                with open(docx_path, "rb") as f:
                    st.download_button(
                        label="Download DOCX",
                        data=f.read(),
                        file_name=f"{filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            except Exception as e:
                st.error(f"Error exporting to DOCX: {str(e)}")
    
    with col2:
        if st.button("📕 Export as PDF"):
            try:
                pdf_path = export_to_pdf(st.session_state.jd, filename)
                st.success(f"✓ Exported to: {pdf_path}")
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="Download PDF",
                        data=f.read(),
                        file_name=f"{filename}.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Error exporting to PDF: {str(e)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Refinement", key="step6_back"):
            st.session_state.step = 5
            st.rerun()
    
    with col2:
        if st.button("🔄 Generate Another JD", key="step6_restart"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.step = 1
            st.rerun()

# ════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════

def main():
    """Main recruiter portal application."""
    st.set_page_config(
        page_title="JD Generator",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = 1
    
    # Header
    st.title("📋 Job Description Generator")
    st.markdown("Professional JD generation powered by LLM")
    
    # Progress bar
    render_step_progress(st.session_state.step)
    
    st.markdown("---")
    
    # Route to appropriate step
    if st.session_state.step == 1:
        render_select_role()
    elif st.session_state.step == 2:
        render_clarify_role()
    elif st.session_state.step == 3:
        render_profile_builder()
    elif st.session_state.step == 4:
        render_draft_jd()
    elif st.session_state.step == 5:
        render_refine_jd()
    elif st.session_state.step == 6:
        render_export()

if __name__ == "__main__":
    main()
