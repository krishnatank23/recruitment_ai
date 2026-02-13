import streamlit as st
import sys
import os
import json
import markdown

# ─────────────────────────────────────────────────────────
# Path setup
# ─────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────
from app.agents.jd_clarifier import generate_clarifying_questions
from app.agents.profile_builder import build_profile
from app.agents.jd_generator import generate_jd
from app.agents.jd_chatbot import refine_jd
from app.utils.llm import get_llm
from app.utils.google_form_loader import fetch_google_form_data
from app.utils.file_export import export_to_docx, export_to_pdf
from datetime import datetime


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
STEP_LABELS = {
    1: ("", "Select role"),
    2: ("", "Clarify"),
    3: ("", "Profile"),
    4: ("", "Draft JD"),
    5: ("", "Refine"),
    6: ("", "Export"),
}

def suggest_role_titles(profile: dict, current_role: str = "") -> list:
    """Suggest 3-5 role titles based on the built profile."""
    profile_json = json.dumps(profile or {}, ensure_ascii=False)
    prompt = f"""
You are a hiring strategist.
Based only on this ideal candidate profile, suggest 3 to 5 professional job titles for the role.
Return only a valid JSON array of strings, no markdown and no explanation.
Keep titles concise and realistic.

Current role title: {current_role}
Profile:
{profile_json}
"""
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        text = content.strip()

        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()

        if "[" in text and "]" in text:
            start = text.find("[")
            end = text.rfind("]") + 1
            text = text[start:end]

        titles = json.loads(text)
        if isinstance(titles, list):
            cleaned = []
            seen = set()
            for t in titles:
                title = str(t).strip()
                if title and title.lower() not in seen:
                    cleaned.append(title)
                    seen.add(title.lower())
            if current_role and current_role.lower() not in seen:
                cleaned.insert(0, current_role)
            return cleaned[:5]
    except Exception:
        pass

    # Fallback suggestions
    base = current_role or str((profile or {}).get("role") or "Role")
    fallback = [
        base,
        f"Senior {base}" if not base.lower().startswith("senior") else base,
        f"{base} Specialist",
        f"{base} Associate",
    ]
    unique = []
    seen = set()
    for item in fallback:
        k = item.strip().lower()
        if item.strip() and k not in seen:
            unique.append(item.strip())
            seen.add(k)
    return unique[:5]

def render_mcq_question(question_id: str, question_text: str, options: list):
    """Render one MCQ in a professional 2-column selectable layout."""
    st.markdown(f'<div class="mcq-question">{clean_display_text(question_text)}</div>', unsafe_allow_html=True)

    existing = st.session_state.clarify_answers.get(question_id, [])
    selected_options = existing if isinstance(existing, list) else []

    for i in range(0, len(options), 2):
        row_cols = st.columns(2, gap="medium")
        for col_idx in range(2):
            opt_idx = i + col_idx
            if opt_idx >= len(options):
                continue
            option = options[opt_idx]
            active = option in selected_options
            icon = "☑" if active else "☐"
            button_label = f"{icon}  {option}"
            button_type = "primary" if active else "secondary"
            with row_cols[col_idx]:
                if st.button(
                    button_label,
                    key=f"mcq_{question_id}_{opt_idx}",
                    use_container_width=True,
                    type=button_type,
                ):
                    current = st.session_state.clarify_answers.get(question_id, [])
                    if not isinstance(current, list):
                        current = []

                    if option in current:
                        current = [x for x in current if x != option]
                    else:
                        current = [*current, option]

                    st.session_state.clarify_answers[question_id] = current

    st.markdown('<div class="mcq-spacer"></div>', unsafe_allow_html=True)


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
        unsafe_allow_html=True,
    )

import re
import html


def clean_display_text(text: str) -> str:
    """
    FINAL UI-SAFE CLEANER
    ---------------------------------
    Fixes:
    - Vertical letter stacking (A\nn\na\nl...)
    - Space-separated letters (A n a l y t i c a l)
    - Hidden unicode characters
    - Excessive whitespace
    - HTML unsafe characters
    """

    if not isinstance(text, str):
        return ""

    # Remove zero-width and hidden unicode chars
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

    # Detect vertical letter stacking
    lines = text.splitlines()
    if len(lines) > 3:
        single_char_lines = sum(1 for l in lines if len(l.strip()) == 1)
        if single_char_lines / len(lines) > 0.6:
            text = "".join(l.strip() for l in lines)

    # Fix space-separated characters like "A n a l y t i c a l"
    if re.match(r"^(\w\s){3,}\w$", text.strip()):
        text = text.replace(" ", "")

    # Replace remaining single newlines with space
    text = text.replace("\n", " ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Escape HTML special characters for safe rendering
    text = html.escape(text)

    return text

def build_full_profile_text(profile: dict) -> str:
    """Create a readable full job profile description for UI display."""
    if not isinstance(profile, dict):
        return ""

    exp = profile.get("experience") or {}
    sm = profile.get("success_metrics") or {}
    we = profile.get("work_environment") or {}

    parts = [
        f"Role: {profile.get('role', '')}",
        f"Department: {profile.get('department', '')}",
        "",
        "Executive Summary:",
        str(profile.get("executive_summary", "")),
        "",
        "Ideal Candidate Portrait:",
        str(profile.get("ideal_candidate_portrait", "")),
        "",
        "Experience:",
        f"- Years: {exp.get('years', '')}",
        f"- Background: {exp.get('background', '')}",
        f"- Ideal Companies: {', '.join(exp.get('ideal_companies', []) or [])}",
        "",
        "Must-have Skills:",
        *[f"- {x}" for x in (profile.get("must_have") or [])],
        "",
        "Nice-to-have Skills:",
        *[f"- {x}" for x in (profile.get("nice_to_have") or [])],
        "",
        "Key Responsibilities:",
        *[f"- {x}" for x in (profile.get("key_responsibilities") or [])],
        "",
        "Success Metrics:",
        f"- First 30 Days: {', '.join(sm.get('first_30_days', []) or [])}",
        f"- First 90 Days: {', '.join(sm.get('first_90_days', []) or [])}",
        f"- First Year: {', '.join(sm.get('first_year', []) or [])}",
        "",
        "Team Fit:",
        str(profile.get("team_fit", "")),
        "",
        "Work Environment:",
        f"- Location: {we.get('location', '')}",
        f"- Team Size: {we.get('team_size', '')}",
        f"- Pace: {we.get('pace', '')}",
        f"- Culture Values: {', '.join(we.get('culture_values', []) or [])}",
        "",
        "Behavioral Traits:",
        str(profile.get("personality_profile", "")),
        "",
        "Dealbreakers:",
        *[f"- {x}" for x in (profile.get("dealbreakers") or [])],
    ]
    return "\n".join(parts).strip()

def step_progress(current: int):
    """Render a visual step progress bar."""
    total = len(STEP_LABELS)
    cols = st.columns(total)
    for i, col in enumerate(cols, start=1):
        icon, label = STEP_LABELS[i]
        if i < current:
            color, bg, border = "#4F46E5", "#EEF2FF", "2px solid #4F46E5"
            check = "✓"
        elif i == current:
            color, bg, border = "white", "#4F46E5", "none"
            check = icon
        else:
            color, bg, border = "#94A3B8", "#F1F5F9", "1px solid #E2E8F0"
            check = icon
        col.markdown(
            f"""
            <div style="text-align:center;">
                <div style="
                    width:42px; height:42px; border-radius:50%;
                    background:{bg}; color:{color}; border:{border};
                    display:inline-flex; align-items:center; justify-content:center;
                    font-size:18px; font-weight:700;
                ">{check}</div>
                <div style="font-size:12px; color:#64748B; margin-top:6px; font-weight:500;">
                    {label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────
def render():
    # ── Styles ──
    st.markdown("""
    <style>
    /* ── Page title ── */
    .page-header {
        text-align: center; margin-bottom: 8px;
    }
    .page-header h1 {
        font-size: 36px !important; font-weight: 800 !important;
        color: #0F172A !important; letter-spacing: -1px;
    }
    .page-header p {
        font-size: 16px; color: #64748B !important; margin-top: -8px;
    }

    /* ── Section cards ── */
    .ui-card {
        background: white; border: 1px solid #E2E8F0;
        border-radius: 14px; padding: 28px 32px;
        margin-bottom: 20px;
    }

    /* ── Section headings inside cards ── */
    .section-heading {
        font-size: 20px !important; font-weight: 700 !important;
        color: #0F172A !important; margin-bottom: 16px !important;
    }

    /* ── Select box ── */
    .stSelectbox > div > div {
        border-radius: 10px !important;
    }

    /* ── Text inputs ── */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 1.5px solid #E2E8F0 !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    }

    /* ── Text area ── */
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 1.5px solid #E2E8F0 !important;
        font-size: 14px !important;
    }

    /* ── Info / success bars ── */
    .stAlert {
        border-radius: 10px !important;
    }

    /* ── FORCE all text dark ── */
    .stMarkdown, .stText, .stCaption,
    p, li, span, label, div,
    h1, h2, h3, h4, h5, h6,
    td, th, caption,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] span,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] div,
    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stTextArea label,
    .stRadio label,
    .stCheckbox label,
    .element-container,
    .stAlert p, .stAlert div {
        color: #1E293B !important;
    }

    /* ── Profile formatting & typography ── */
    .profile-section {
        font-family: 'Inter', sans-serif;
        color: #0F172A;
        font-size: 15px;
        line-height: 1.6;
        margin-bottom: 14px;
    }
    .profile-section h4 {
        font-size: 16px; margin: 0 0 8px 0; color: #0F172A; font-weight:700;
    }
    .profile-section p { margin: 0 0 8px 0; }
    .profile-section ul { margin: 6px 0 8px 18px; padding: 0; }
    .profile-section ul li { margin-bottom:6px; }

    /* prevent single-character wrapping */
    .profile-section, .profile-section * {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
        white-space: normal !important;
        letter-spacing: normal !important;
    }

    .profile-chip { white-space: nowrap; }

    /* ── Ensure columns/containers preserve text wrapping ── */
    [data-testid="column"] {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    [data-testid="column"] p, [data-testid="column"] span, [data-testid="column"] div {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        white-space: normal !important;
    }

    /* ── Select / multiselect dropdowns ── */
    [data-testid="stSelectbox"] div,
    [data-testid="stSelectbox"] span,
    [data-testid="stSelectbox"] input,
    [data-testid="stMultiSelect"] div,
    [data-testid="stMultiSelect"] span,
    [data-testid="stMultiSelect"] input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        color: #1E293B !important;
    }

    /* ── Text input value ── */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        color: #1E293B !important;
    }

    /* ── Expander header ── */
    [data-testid="stExpander"] details summary span {
        color: #1E293B !important;
    }

    /* ── Download buttons text ── */
    .stDownloadButton button {
        color: white !important;
    }

    /* ── Caption ── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #64748B !important;
    }

    /* ── Dividers ── */
    hr {
        border: none; border-top: 1px solid #E2E8F0; margin: 20px 0;
    }

    /* ── Chat bubbles ── */
    .chat-bubble-user {
        background: #EEF2FF; border-radius: 12px;
        padding: 12px 16px; margin: 6px 0;
        color: #3730A3 !important; font-size: 14px;
    }
    .chat-bubble-system {
        background: #F0FDF4; border-radius: 12px;
        padding: 10px 16px; margin: 6px 0;
        color: #166534 !important; font-size: 13px;
    }

    /* ── Profile chips ── */
    .profile-chip {
        display: inline-block;
        background: #EEF2FF;
        color: #4338CA !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        margin: 4px 4px 4px 0;
    }

    /* ── MCQ layout ── */
    .mcq-question {
        font-size: 15px;
        font-weight: 600;
        color: #0F172A !important;
        margin: 6px 0 10px 0;
    }
    .mcq-spacer {
        height: 12px;
    }
    div.stButton > button[kind="secondary"] {
        background: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        color: #334155 !important;
        border-radius: 8px !important;
        text-align: left !important;
        min-height: 42px !important;
        font-weight: 500 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #94A3B8 !important;
        background: #F1F5F9 !important;
    }
    div.stButton > button[kind="primary"] {
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Session state defaults ──
    defaults = {
        "step": 1,
        "selected_role": None,
        "jd_data": {},
        "clarify_questions": [],
        "clarify_answers": {},
        "profile": {},
        "role_title_suggestions": [],
        "selected_suggested_title": None,
        "draft_jd": "",
        "final_jd": "",
        "chat_history": [],
        "chatbot_session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Header ──
    st.markdown("""
    <div class="page-header">
        <h1>JD generator</h1>
        <p>Create professional job descriptions in 6 easy steps</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Progress bar ──
    step_progress(st.session_state.step)

    # ═══════════════════════════════════════════════════════
    # STEP 1 — Select Role
    # ═══════════════════════════════════════════════════════
    if st.session_state.step == 1:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Select a Job Role</div>', unsafe_allow_html=True)

        try:
            roles = fetch_google_form_data() or []
        except Exception as e:
            st.error("❌ Unable to load roles from Google Sheet right now.")
            st.info(f"Connection issue: {str(e)}")
            st.stop()

        if not roles:
            st.error("❌ No roles found. Check Google Sheet data/configuration.")
            st.stop()

        role_names = [r["role"] for r in roles]
        default_idx = role_names.index(st.session_state.selected_role) if st.session_state.selected_role in role_names else 0

        selected_role = st.selectbox("Job Role", role_names, index=default_idx, label_visibility="collapsed")

        if selected_role:
            role_data = next(r for r in roles if r["role"] == selected_role)
            if st.session_state.selected_role != selected_role:
                st.session_state.role_title_suggestions = []
                st.session_state.selected_suggested_title = None
            st.session_state.selected_role = selected_role
            st.session_state.jd_data = role_data

            # Show quick info
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Department:** {role_data.get('department', '—')}")
            c2.markdown(f"**📍 Location:** {role_data.get('location', '—')}")
            c3.markdown(f"**⏱️ Experience:** {role_data.get('experience', '—')}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Navigation
        _, rc = st.columns([3, 1])
        with rc:
            if st.session_state.selected_role:
                if st.button("Continue →", use_container_width=True, type="primary"):
                    st.session_state.step = 2
                    st.rerun()


    # ═══════════════════════════════════════════════════════
    # STEP 2 — Clarifying Questions (Agent 1)
    # ═══════════════════════════════════════════════════════
    elif st.session_state.step == 2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Clarify the Role</div>', unsafe_allow_html=True)
        st.caption("Answer these questions to help us build a more accurate candidate profile.")

        if not st.session_state.clarify_questions:
            with st.spinner("Generating clarifying questions..."):
                try:
                    st.session_state.clarify_questions = generate_clarifying_questions(
                        form_data=st.session_state.jd_data
                    ) or []
                except Exception:
                    st.session_state.clarify_questions = []

        if not st.session_state.clarify_questions:
            st.error("Could not generate clarifying questions. Proceeding without clarifications.")
            proceed_without_clarify = True
        else:
            proceed_without_clarify = False

            # Display and collect answers for clarifying questions
            for q in st.session_state.clarify_questions:
                q_id = q.get("id", "q1")
                q_text = q.get("question", "")
                q_options = q.get("options", [])
                if not q_options:
                    st.warning(f"No options available for: {q_text}")
                    continue

                render_mcq_question(
                    question_id=q_id,
                    question_text=q_text,
                    options=q_options,
                )

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        total_questions = len(st.session_state.clarify_questions)
        answered_questions = 0
        for q in st.session_state.clarify_questions:
            q_id = q.get("id", "q1")
            if st.session_state.clarify_answers.get(q_id):
                answered_questions += 1
        if total_questions > 0:
            st.caption(f"Answered {answered_questions}/{total_questions} questions (optional)")

        lc, _, rc = st.columns([1, 2, 1])
        with lc:
            if st.button("← Back", use_container_width=True, type="secondary"):
                st.session_state.clarify_questions = []
                st.session_state.clarify_answers = {}
                st.session_state.step = 1
                st.rerun()
        with rc:
            if st.button("Continue to Profile →", use_container_width=True, type="primary"):
                st.session_state.step = 3
                st.rerun()


    # ═══════════════════════════════════════════════════════
    # STEP 3 — Profile Builder (Agent 2)
    # ═══════════════════════════════════════════════════════
    elif st.session_state.step == 3:

        if not st.session_state.profile:
            with st.spinner("Building ideal candidate profile..."):
                try:
                    clarification_answers_formatted = []
                    for q in st.session_state.clarify_questions:
                        q_id = q.get("id")
                        clarification_answers_formatted.append({
                            "id": q_id,
                            "question": q.get("question"),
                            "answer": st.session_state.clarify_answers.get(q_id, [])
                        })

                    st.session_state.profile = build_profile(
                        form_data=st.session_state.jd_data,
                        clarification_answers=clarification_answers_formatted,
                    )

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    st.error(f"❌ Failed to build profile: {str(e)}")
                    st.stop()

        p = st.session_state.profile

        if not st.session_state.role_title_suggestions:
            st.session_state.role_title_suggestions = suggest_role_titles(
                profile=p,
                current_role=st.session_state.selected_role or st.session_state.jd_data.get("role", ""),
            )

        # ---------- HEADER ----------
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #6366F1, #8B5CF6);
                color: white; border-radius: 14px; padding: 24px 32px;
                margin-bottom: 20px;
            ">
                <div style="font-size:22px; font-weight:700; color:white !important;">
                    Ideal Candidate Profile
                </div>
                <div style="font-size:14px; opacity:0.85; margin-top:4px; color:white !important;">
                    {clean_display_text(p.get('role', ''))} —
                    {clean_display_text(p.get('department', ''))} Department
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Full profile text (complete description, not title-only)
        full_profile_text = build_full_profile_text(p)
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Full Job Profile Description</div>', unsafe_allow_html=True)
        st.text_area(
            "Complete profile text",
            value=full_profile_text,
            height=320,
            disabled=True,
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">Suggested Job Titles</div>', unsafe_allow_html=True)
        st.caption("Choose the best-fit title for this profile. This will be applied to JD generation and export.")
        title_options = st.session_state.role_title_suggestions or [st.session_state.selected_role]
        current_title = st.session_state.selected_role or st.session_state.jd_data.get("role", "")
        if current_title and current_title not in title_options:
            title_options = [current_title, *title_options]

        default_idx = 0
        if st.session_state.selected_suggested_title in title_options:
            default_idx = title_options.index(st.session_state.selected_suggested_title)
        elif current_title in title_options:
            default_idx = title_options.index(current_title)

        chosen_title = st.selectbox(
            "Recommended title",
            options=title_options,
            index=default_idx,
            key="role_title_selector",
            label_visibility="collapsed",
        )

        apply_col, refresh_col = st.columns([1, 1])
        with apply_col:
            if st.button("Apply Selected Title", use_container_width=True, type="primary"):
                st.session_state.selected_suggested_title = chosen_title
                st.session_state.selected_role = chosen_title
                st.session_state.jd_data["role"] = chosen_title
                st.session_state.profile["role"] = chosen_title
                st.success(f"Applied role title: {chosen_title}")
                st.rerun()
        with refresh_col:
            if st.button("Refresh Suggestions", use_container_width=True, type="secondary"):
                st.session_state.role_title_suggestions = suggest_role_titles(
                    profile=st.session_state.profile,
                    current_role=st.session_state.selected_role or st.session_state.jd_data.get("role", ""),
                )
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- EXEC SUMMARY ----------
        exec_summary = clean_display_text(
            p.get("executive_summary") or p.get("profile_summary", "—")
        )

        portrait = clean_display_text(
            p.get("ideal_candidate_portrait", "—")
        )

        st.markdown(
            f"""
            <div class="profile-section">
                <h4>Executive Summary</h4>
                <p>{exec_summary}</p>
            </div>

            <div class="profile-section">
                <h4>Ideal Candidate Portrait</h4>
                <p>{portrait}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---------- TWO COLUMNS ----------
        c1, c2 = st.columns(2)

        # ================= LEFT COLUMN =================
        with c1:

            exp = p.get("experience") or {}

            ideal_companies = exp.get("ideal_companies") or []
            companies_html = ""
            if ideal_companies:
                companies_html = f"""
                <li><strong>Ideal companies:</strong>
                {clean_display_text(", ".join(ideal_companies))}
                </li>
                """

            st.markdown(
                f"""
                <div class="profile-section">
                    <h4>Experience & Background</h4>
                    <ul>
                        <li><strong>Years:</strong>
                            {clean_display_text(exp.get('years', '—'))}
                        </li>
                        <li><strong>Background:</strong>
                            {clean_display_text(exp.get('background', '—'))}
                        </li>
                        {companies_html}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Must-have
            must_have = p.get("must_have") or []
            st.markdown(
                f"""
                <div class="profile-section">
                    <h4>Must-have Skills</h4>
                    <ul>
                        {''.join(f'<li>{clean_display_text(item)}</li>' for item in must_have)}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Nice-to-have
            nice = p.get("nice_to_have") or []
            st.markdown(
                f"""
                <div class="profile-section">
                    <h4>Nice-to-have</h4>
                    <ul>
                        {''.join(f'<li>{clean_display_text(item)}</li>' for item in nice)}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ================= RIGHT COLUMN =================
        with c2:

            # ✅ FIXED HERE — prevent NoneType iterable error
            personality = p.get("personality_profile") or []

            if isinstance(personality, str):
                personality = [personality]

            if not isinstance(personality, list):
                personality = []

            st.markdown(
                f"""
                <div class="profile-section">
                    <h4>Behavioral Traits</h4>
                    <div style="display:flex;flex-wrap:wrap;gap:8px;">
                        {''.join(
                            f'<span class="profile-chip">{clean_display_text(item)}</span>'
                            for item in personality if item
                        )}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            we = p.get("work_environment") or {}
            culture = we.get("culture_values") or []

            st.markdown(
                f"""
                <div class="profile-section">
                    <h4>Work Environment</h4>
                    <ul>
                        <li><strong>Location:</strong>
                            {clean_display_text(we.get('location', '—'))}
                        </li>
                        <li><strong>Team size:</strong>
                            {clean_display_text(we.get('team_size', '—'))}
                        </li>
                        <li><strong>Pace:</strong>
                            {clean_display_text(we.get('pace', '—'))}
                        </li>
                        {"<li><strong>Culture:</strong> " + clean_display_text(', '.join(culture)) + "</li>" if culture else ""}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            dealbreakers = p.get("dealbreakers") or []
            if dealbreakers:
                st.markdown(
                    f"""
                    <div class="profile-section">
                        <h4>Dealbreakers</h4>
                        <ul>
                            {''.join(f'<li>{clean_display_text(d)}</li>' for d in dealbreakers)}
                        </ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ---------- RESPONSIBILITIES ----------
        st.markdown("<h4>Key Responsibilities</h4>", unsafe_allow_html=True)
        for item in p.get("key_responsibilities") or []:
            st.markdown(f"- {clean_display_text(item)}")

        # ---------- SUCCESS METRICS ----------
        st.markdown("---")
        st.markdown("### 📊 Success Metrics")

        sm = p.get("success_metrics") or {}

        st.markdown(
            f"- 30 days: {clean_display_text(', '.join(sm.get('first_30_days') or []) or '—')}"
        )
        st.markdown(
            f"- 90 days: {clean_display_text(', '.join(sm.get('first_90_days') or []) or '—')}"
        )
        st.markdown(
            f"- 1 year: {clean_display_text(', '.join(sm.get('first_year') or []) or '—')}"
        )

        # Raw JSON view
        with st.expander("View full profile JSON", expanded=False):
            st.json(p)

        # Navigation
        lc, _, rc = st.columns([1, 2, 1])
        with lc:
            if st.button("← Back", use_container_width=True, type="secondary"):
                st.session_state.profile = {}
                st.session_state.role_title_suggestions = []
                st.session_state.selected_suggested_title = None
                st.session_state.step = 2
                st.rerun()

        with rc:
            if st.button("Generate JD →", use_container_width=True, type="primary"):
                st.session_state.step = 4
    # ═══════════════════════════════════════════════════════
    # STEP 4 — Draft JD (Agent 3)
    # ═══════════════════════════════════════════════════════
    elif st.session_state.step == 4:
        if not st.session_state.draft_jd:
            with st.spinner("Generating job description from profile..."):
                st.session_state.draft_jd = generate_jd(
                    form_data=st.session_state.jd_data,
                    profile=st.session_state.profile,
                )
                st.session_state.final_jd = st.session_state.draft_jd

        st.success("✅ Draft JD generated! Review it below, then proceed to refine.")
        render_jd_html(st.session_state.final_jd)

        # Navigation
        st.markdown("")
        lc, _, rc = st.columns([1, 2, 1])
        with lc:
            if st.button("← Back to Profile", use_container_width=True, type="secondary"):
                st.session_state.draft_jd = ""
                st.session_state.final_jd = ""
                st.session_state.step = 3
                st.rerun()
        with rc:
            if st.button("Refine with Chat →", use_container_width=True, type="primary"):
                st.session_state.step = 5

    # ═══════════════════════════════════════════════════════
    # STEP 5 — Chatbot Loop (Agent 4)
    # ═══════════════════════════════════════════════════════
    elif st.session_state.step == 5:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-heading">Refine your JD</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Type an instruction below and click **Apply**. "
            "Each time you apply, a new version is generated. "
            "Click **Finalize** when you're happy."
        )

        # Chat history
        for entry in st.session_state.chat_history:
            st.markdown(
                f'<div class="chat-bubble-user"><b>You:</b> {entry["instruction"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="chat-bubble-system">✅ Applied — version {entry["version"]}</div>',
                unsafe_allow_html=True,
            )

        # Input row
        ic, bc = st.columns([5, 1])
        with ic:
            instruction = st.text_input(
                "Instruction",
                placeholder="e.g. Make it more concise / Add Python requirement / Remove travel section",
                key="chat_input",
                label_visibility="collapsed",
            )
        with bc:
            apply = st.button("Apply", type="primary", use_container_width=True)

        if apply and instruction and instruction.strip():
            with st.spinner("Applying changes..."):
                updated = refine_jd(
                    current_jd=st.session_state.final_jd,
                    instruction=instruction.strip(),
                    role=st.session_state.selected_role,
                    session_id=st.session_state.chatbot_session_id,
                )
                st.session_state.final_jd = updated
                st.session_state.chat_history.append({
                    "instruction": instruction.strip(),
                    "version": len(st.session_state.chat_history) + 1,
                    "timestamp": datetime.now().isoformat(),
                })
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # JD Preview
        st.markdown("")
        with st.expander("Current JD preview", expanded=True):
            render_jd_html(st.session_state.final_jd)

        # Navigation
        st.markdown("")
        lc, _, rc = st.columns([1, 2, 1])
        with lc:
            if st.button("← Back to Draft", use_container_width=True, type="secondary"):
                st.session_state.step = 4
                st.rerun()
        with rc:
            if st.button("Finalize & Export →", use_container_width=True, type="primary"):
                st.session_state.step = 6
                st.rerun()

    # ═══════════════════════════════════════════════════════
    # STEP 6 — Final Export (Agent 5)
    # ═══════════════════════════════════════════════════════
    elif st.session_state.step == 6:
        st.success("Your job description is ready")

        # Preview
        render_jd_html(st.session_state.final_jd)

        # Optional manual edit
        with st.expander("✏️ Manual Edit (optional)"):
            edited = st.text_area(
                "Edit JD",
                value=st.session_state.final_jd,
                height=350,
                label_visibility="collapsed",
            )
            if edited != st.session_state.final_jd:
                st.session_state.final_jd = edited

        # Downloads
        st.markdown("---")
        st.markdown("**Download your JD**")
        filename = st.session_state.selected_role.replace(" ", "_") + "_JD"

        dc, pc = st.columns(2)
        with dc:
            docx_path = export_to_docx(st.session_state.final_jd, filename)
            with open(docx_path, "rb") as f:
                st.download_button(
                    "Download DOCX",
                    f,
                    file_name=f"{filename}.docx",
                    use_container_width=True,
                    type="primary",
                )
        with pc:
            pdf_path = export_to_pdf(st.session_state.final_jd, filename)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Download PDF",
                    f,
                    file_name=f"{filename}.pdf",
                    use_container_width=True,
                    type="primary",
                )

        # Log info
        if st.session_state.chat_history:
            st.caption(
                f"💾 {len(st.session_state.chat_history)} refinement(s) saved to "
                f"`exports/chatbot_logs/{st.session_state.chatbot_session_id}.json`"
            )

        # Start over
        st.markdown("---")
        if st.button("Create another JD", use_container_width=True, type="secondary"):
            for k in list(st.session_state.keys()):
                if k != "page":
                    del st.session_state[k]
            st.session_state.step = 1
            st.rerun()
