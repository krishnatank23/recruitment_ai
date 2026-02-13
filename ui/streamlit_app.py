# streamlit_app.py  —  Main entry point
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="WOGOM Hiring Platform",
    layout="wide",
    page_icon="WOGOM",
    initial_sidebar_state="collapsed",
)

# ── Import portals ──────────────────────────────────────────
try:
    import recruiter_portal
    # import candidate_portal
    import candidate_matching_portal
except ModuleNotFoundError:
    from ui import recruiter_portal, candidate_matching_portal

# ── Global Design System ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none; }

/* ── Page background ── */
.stApp {
    background: #F8FAFC;
}

/* ── FORCE dark text on all elements ── */
.stMarkdown, .stText, .stCaption, .stAlert,
p, li, span, label, div,
h1, h2, h3, h4, h5, h6,
td, th, caption,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stCaptionContainer"],
[data-testid="stExpander"] summary,
[data-testid="stExpander"] div,
.stSelectbox label,
.stMultiSelect label,
.stTextInput label,
.stTextArea label,
.stRadio label,
.stCheckbox label,
.stFileUploader label,
.stFileUploader span,
.stAlert p,
.element-container {
    color: #1E293B !important;
}

/* ── Select box / multiselect text ── */
[data-testid="stSelectbox"] div,
[data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] div,
[data-testid="stMultiSelect"] span,
.stSelectbox > div > div,
.stMultiSelect > div > div {
    color: #1E293B !important;
}

/* ── Info / warning / success alerts ── */
.stAlert > div {
    color: #1E293B !important;
}

/* ── Expander headers ── */
[data-testid="stExpander"] details summary span {
    color: #1E293B !important;
}

/* ── Spinner text ── */
.stSpinner > div {
    color: #1E293B !important;
}

/* ── Nav bar ── */
.nav-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 48px;
    background: white;
    border-bottom: 1px solid #E2E8F0;
    margin: -1rem -1rem 0 -1rem;
}
.nav-logo {
    font-size: 24px;
    font-weight: 800;
    color: #4F46E5 !important;
    letter-spacing: -0.5px;
}
.nav-links a {
    margin-left: 28px;
    font-size: 15px;
    font-weight: 500;
    color: #64748B !important;
    text-decoration: none;
}

/* ── Hero (refined, minimal & professional) ── */
.hero {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 88px 24px 72px;
}
.hero-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(250,250,252,0.95));
    border-radius: 20px;
    box-shadow: 0 12px 40px rgba(2,6,23,0.06);
    padding: 56px 48px;
    max-width: 1100px;
    width: 100%;
    text-align: center;
    border: 1px solid rgba(15,23,42,0.04);
}
.hero .kicker {
    display: inline-block;
    font-size: 13px;
    color: #7C82A1;
    letter-spacing: 1px;
    text-transform: uppercase;
    background: rgba(99,102,241,0.06);
    padding: 6px 10px;
    border-radius: 999px;
    margin-bottom: 18px;
}
.hero h1 {
    font-size: 48px !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    letter-spacing: -0.6px;
    line-height: 1.05;
    margin: 0.15rem 0 16px !important;
}
.hero h1 .accent {
    background: linear-gradient(90deg, #6D28D9 0%, #8B5CF6 50%, #7C3AED 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero h1 .link-icon {
    display: inline-block;
    margin-left: 8px;
    vertical-align: middle;
    color: #94A3B8;
    font-size: 18px;
}
.hero p {
    font-size: 16px;
    color: #475569 !important;
    line-height: 1.7;
    max-width: 820px;
    margin: 0 auto 22px;
}
.hero-ctas {
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 18px;
}
.hero-cta-primary {
    background: linear-gradient(90deg,#6D28D9,#8B5CF6) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 12px 22px !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 30px rgba(99,102,241,0.12) !important;
}
.hero-cta-ghost {
    background: transparent !important;
    color: #334155 !important;
    border: 1px solid rgba(15,23,42,0.06) !important;
    border-radius: 12px !important;
    padding: 12px 22px !important;
    font-weight: 600 !important;
}
@media (max-width: 640px) {
    .hero-card { padding: 36px 20px; }
    .hero h1 { font-size: 32px !important; }
    .hero p { font-size: 14px; }
}


/* ── Feature cards ── */
.features {
    display: flex;
    gap: 24px;
    max-width: 900px;
    margin: 0 auto 60px;
    padding: 0 24px;
}
.feature-card {
    flex: 1;
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 32px;
    transition: all 0.2s ease;
}
.feature-card:hover {
    border-color: #6366F1;
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.1);
    transform: translateY(-4px);
}
.feature-icon {
    font-size: 36px;
    margin-bottom: 16px;
}
.feature-card h3 {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    margin-bottom: 8px !important;
}
.feature-card p {
    font-size: 15px;
    color: #64748B !important;
    line-height: 1.5;
}

/* ── Buttons ── */
div.stButton > button {
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    border: none;
    transition: all 0.2s ease;
}
div.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    color: white !important;
}
div.stButton > button[data-testid="stBaseButton-primary"]:hover {
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    transform: translateY(-1px);
}
div.stButton > button[data-testid="stBaseButton-secondary"] {
    background: white !important;
    color: #4F46E5 !important;
    border: 1.5px solid #E2E8F0 !important;
}

/* ── Back button on sub-pages ── */
.back-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #6366F1 !important;
    font-weight: 600;
    font-size: 15px;
    cursor: pointer;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ───────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ═══════════════════════════════════════════════════════════
# HOME PAGE
# ═══════════════════════════════════════════════════════════
if st.session_state.page == "Home":

    # Nav bar
    st.markdown("""
    <div class="nav-bar">
        <div class="nav-logo">WOGOM</div>
        <div class="nav-links">
            <a href="#">Platform</a>
            <a href="#">About</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hero (refined)
    st.markdown("""
    <div class="hero">
      <div class="hero-card">
        <div class="kicker">Smart Hiring</div>
        <h1>Smart Hiring,<br/><span class="accent">Powered by AI</span></h1>
        <p>Generate professional job descriptions, analyze candidates with persona-driven fit scoring, and make data-driven hiring decisions — all in one minimal, secure platform.</p>
        <div class="hero-ctas">
          <button class="hero-cta-primary" onclick="window.location.href='#'">Start JD creation</button>
          <button class="hero-cta-ghost" onclick="window.location.href='#'">Explore candidates</button>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature Cards
    st.markdown("""
    <div class="features">
        <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>JD generator</h3>
            <p>Create hiring-ready job descriptions in minutes using
            AI-powered clarifying questions and profile building.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>Candidate Intelligence</h3>
            <p>Match resumes to AI-generated personas and get detailed
            fit scores with strengths, gaps, and recommendations.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if st.button("Start JD creation", use_container_width=True, type="primary"):
                st.session_state.page = "Recruiter"
                st.rerun()
        with c2:
            if st.button("Match Candidates", use_container_width=True, type="primary"):
                st.session_state.page = "CandidateMatching"
                st.rerun()

# ═══════════════════════════════════════════════════════════
# RECRUITER PAGE
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "Recruiter":
    if st.button("← Back to Home", type="secondary"):
        st.session_state.page = "Home"
        # Reset recruiter state
        for k in list(st.session_state.keys()):
            if k != "page":
                del st.session_state[k]
        st.rerun()
    recruiter_portal.render()

# ═══════════════════════════════════════════════════════════
# CANDIDATE PAGE
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "Candidate":
    if st.button("← Back to Home", type="secondary"):
        st.session_state.page = "Home"
        st.rerun()
    candidate_portal.render()

# ═══════════════════════════════════════════════════════════
# CANDIDATE MATCHING PAGE (NEW)
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "CandidateMatching":
    if st.button("← Back to Home", type="secondary"):
        st.session_state.page = "Home"
        # Reset candidate matching state
        for k in list(st.session_state.keys()):
            if k != "page":
                del st.session_state[k]
        st.rerun()
    candidate_matching_portal.main()