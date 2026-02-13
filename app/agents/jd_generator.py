# app/agents/jd_generator.py
# Agent 3: JD Generator
# Generates a professional JD using the Profile Builder output as ground truth

import sys
import os
import re
from typing import Dict

# --------------------------------------------------
# Project path setup
# --------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --------------------------------------------------
# Imports
# --------------------------------------------------
try:
    from app.utils.llm import get_llm
    from app.utils.constants import ABOUT_WOGOM_TEXT, WOGOM_BRAND
except ImportError as e:
    print(f"[JD_GENERATOR] Warning: {e}")
    ABOUT_WOGOM_TEXT = "About WOGOM information unavailable."
    WOGOM_BRAND = {}

    def get_llm():
        class MockLLM:
            def invoke(self, prompt):
                class MockResponse:
                    content = f"Mock JD generated for prompt: {prompt[:160]}..."
                return MockResponse()
        return MockLLM()


# --------------------------------------------------
# Helper
# --------------------------------------------------
def _format_experience(exp_raw: str) -> str:
    """Return a human-friendly experience phrase."""
    if not exp_raw:
        return "Not specified"

    s = str(exp_raw).strip()
    s_lower = s.lower()

    m_range = re.search(r'(\d+\s*[-–]\s*\d+)', s)
    if m_range:
        span = m_range.group(1).replace(" ", "")
        return f"Approximately {span} years" if "year" not in s_lower else f"Approximately {span}"

    m_num = re.search(r'(\d+)\+?', s)
    if m_num:
        val = m_num.group(1)
        if "year" in s_lower:
            return f"Relevant experience of {val} years or equivalent"

    return s


# --------------------------------------------------
# Prompt (uses Profile Builder output)
# --------------------------------------------------
JD_GENERATOR_PROMPT = """
Create a professional Job Description for WOGOM using the structure below.
You are given an "Ideal Candidate Profile" built by our Profile Builder agent — use it as your PRIMARY source of truth.

CONTEXT:
- Role: {role}
- Department: {department}
- Profile Built From: {profile_context}

COMPANY BRAND GUIDELINES:
Mission: {mission}
Vision: {vision}
Tone: {tone}
Culture: {culture}
Language Rules: {language_rules}

# {role}

Location: {location}
Type: {employment_type}

## About Us
{about_wogom}

## Role Overview
Write 2–3 sentences explaining the role's purpose and direct impact on WOGOM's mission.
Use the Profile Summary from the Ideal Candidate Profile below.

## Key Responsibilities
Use the "key_responsibilities" from the Profile as ground truth.
Write 5–7 bullets. Each bullet: MAXIMUM 1 to 1.5 lines (ONE concise sentence, max 15-20 words).
Start with "• ".
Focus on the core actions and outcomes specific to this {role} in {department}.

## Requirements

### Must-Have Skills
Use "must_have" from the Profile.
Write 4–6 bullets. Each bullet: ONE to TWO concise sentences explaining proficiency and why it matters for this role.

### Nice-to-Have Skills
Use "nice_to_have" from the Profile.
2–3 bullets.

## Who Will Succeed in This Role
Use "personality_profile" and "dealbreakers" from the Profile.
Write 2–3 sentences about the mindset, behaviors, and traits needed for this {role}.

─────────────────────────────
IDEAL CANDIDATE PROFILE (PRIMARY SOURCE):
{profile_json}
─────────────────────────────

GOOGLE FORM DATA (SECONDARY SOURCE):
{facts}
─────────────────────────────

RULES:
- The Profile is your PRIMARY source. The form data is SECONDARY (for any missing details).
- KEEP KEY RESPONSIBILITIES SHORT (max 1–1.5 lines per bullet).
- Use "• " for bullets. Each bullet on new line.
- USE THIS EXACT HEADING ORDER:
  1) # {role}
  2) Location / Type
  3) ## About Us
  4) ## Role Overview
  5) ## Key Responsibilities
  6) ## Requirements
  7) ### Must-Have Skills
  8) ### Nice-to-Have Skills
  9) ## Who Will Succeed in This Role
- Follow WOGOM tone: professional, clear, no jargon.
- Do NOT add extra sections or subsections.
- Output ONLY the formatted JD.
"""


# --------------------------------------------------
# Normalize bullets
# --------------------------------------------------
def normalize_bullets(text: str) -> str:
    # Split inline bullets into separate lines (e.g., "A • B • C")
    text = re.sub(r"\s+[•\u2022]\s+", r"\n• ", text)
    text = re.sub(r"\s+-\s+(?=[A-Za-z])", r"\n• ", text)

    # Ensure major headings are on their own lines
    text = re.sub(r"\s*(##\s+Key Responsibilities)\s*", r"\n\n\1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(##\s+Requirements)\s*", r"\n\n\1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(###\s+Must-Have Skills)\s*", r"\n\n\1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(###\s+Nice-to-Have Skills)\s*", r"\n\n\1\n", text, flags=re.IGNORECASE)

    lines = []
    for line in text.splitlines():
        line = line.rstrip()
        stripped = line.lstrip()
        if stripped.startswith(("-", "*")) and not stripped.startswith(("##", "#")):
            content = stripped.lstrip("-* ").strip()
            lines.append("• " + content)
            continue
        if stripped.startswith("•"):
            content = stripped.lstrip("• ").strip()
            lines.append("• " + content)
            continue
        lines.append(line)
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized

def _ensure_jd_structure(content: str, role: str, location: str, experience_phrase: str, employment_type: str, department: str) -> str:
    """Guarantee draft JD has the same core structure as final JD."""
    text = (content or "").strip()
    if not text:
        text = f"# {role}"

    required_blocks = [
        f"# {role}",
        f"Location: {location}",
        f"Experience: {experience_phrase}",
        f"Type: {employment_type}",
        f"Department: {department}",
        "## About Us",
        "## Role Overview",
        "## Key Responsibilities",
        "## Requirements",
        "### Must-Have Skills",
        "### Nice-to-Have Skills",
        "## Who Will Succeed in This Role",
    ]

    # Ensure title is standardized at the top
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        text = f"# {role}\n\n{text}".strip()
    elif lines[0].strip() != f"# {role}":
        lines[0] = f"# {role}"
        text = "\n".join(lines)

    # Append missing required blocks
    for block in required_blocks[1:]:
        if block not in text:
            if block.startswith("## ") or block.startswith("### "):
                text += f"\n\n{block}\n"
            else:
                text += f"\n{block}"

    return text.strip()


# --------------------------------------------------
# JD GENERATOR (MAIN AGENT)
# --------------------------------------------------
def generate_jd(form_data: Dict, profile: Dict = None) -> str:
    """
    Agent 3: Generates a hiring-ready JD.

    Args:
        form_data: dict from Google Form (role, department, skills, etc.)
        profile: dict from Profile Builder (Agent 2). If None, falls back to form_data only.

    Returns:
        str: The generated JD text in markdown format.
    """
    import json

    data = form_data.copy()

    # Required fields
    REQUIRED_FIELDS = ["role", "employment_type"]
    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        raise ValueError(f"Missing required JD fields: {missing}")

    # Defaults
    data["ctc"] = data.get("salary") or "As per company standards"
    data["location"] = data.get("location") or "India"
    data["joining_time"] = data.get("joining_time") or "As per company requirement"
    data["reporting_to"] = data.get("reporting_to") or "Reporting Manager"

    # Build facts block
    facts_lines = []
    keys_for_facts = [
        "role", "department", "location", "experience", "employment_type",
        "work_mode", "travel_required", "reporting_to", "salary", "urgency",
        "must_have_skills", "other_skills", "key_responsibilities", "minimum_education"
    ]
    for key in keys_for_facts:
        val = data.get(key)
        if val:
            if isinstance(val, list):
                facts_lines.append(f"{key}: {', '.join(val)}")
            else:
                facts_lines.append(f"{key}: {val}")

    for key, value in data.items():
        if key not in keys_for_facts and value:
            if isinstance(value, list):
                facts_lines.append(f"{key}: {', '.join(value)}")
            else:
                facts_lines.append(f"{key}: {value}")

    facts = "\n".join(facts_lines)
    if not facts.strip():
        raise ValueError("FACTS block is empty — Google Form data not loaded")

    # Brand pieces
    mission = WOGOM_BRAND.get("mission", "")
    vision = WOGOM_BRAND.get("vision", "")
    tone = WOGOM_BRAND.get("tone", "")
    culture = ", ".join(WOGOM_BRAND.get("culture", []))
    language_rules = ", ".join(WOGOM_BRAND.get("language_rules", []))

    # Experience
    experience_phrase = _format_experience(data.get("experience", ""))
    
    # Department and profile context
    department = data.get("department", "Not specified")
    profile_source = "Profile Builder (Agent 2) + Form Data" if profile else "Google Form Data Only"

    # Profile JSON (from Agent 2)
    profile_json = json.dumps(profile, indent=2) if profile else "{}"

    prompt = JD_GENERATOR_PROMPT.format(
        mission=mission,
        vision=vision,
        tone=tone,
        culture=culture,
        language_rules=language_rules,
        role=data["role"],
        department=department,
        profile_context=profile_source,
        location=data["location"],
        experience_phrase=experience_phrase,
        employment_type=data["employment_type"],
        about_wogom=ABOUT_WOGOM_TEXT.strip(),
        profile_json=profile_json,
        facts=facts
    )

    # LLM call
    llm = get_llm()
    response = llm.invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            part.get("text", str(part))
            if isinstance(part, dict)
            else str(part)
            for part in content
        )

    content = normalize_bullets(content)
    content = _ensure_jd_structure(
        content=content,
        role=data["role"],
        location=data["location"],
        experience_phrase=experience_phrase,
        employment_type=data["employment_type"],
        department=department,
    )
    return content.strip()
