# =========================================================
# app/agents/profile_builder.py
# Agent 2: Strategic Job Profile Builder
# Generates a detailed JOB PROFILE (NOT candidate persona)
# =========================================================

import json
import re
from typing import Dict, Any, List
from app.utils.llm import get_llm


# =========================================================
# PROMPT
# =========================================================

JOB_PROFILE_PROMPT = """
You are a senior HR strategist building an "Ideal Candidate Profile" for recruitment and persona matching.

ROLE: "{role}"
DEPARTMENT: "{department}"

YOUR TASK:
Generate a comprehensive Ideal Candidate Profile JSON that describes the PERFECT candidate for this role.
This profile will be used to generate job-matching personas and grade resumes.

RULES:
- Return STRICT valid JSON ONLY
- No markdown, no explanations, no code blocks
- Every field must exist (use "" for empty strings, [] for empty arrays)
- Be specific and data-driven based on form_data and clarifications
- Focus on candidate fit, not job description
- Make summaries 2-3 sentences max

INPUTS:
FORM DATA: {form_data}
CLARIFICATION ANSWERS: {clarification_answers}

REQUIRED OUTPUT SCHEMA:

{{
  "role": "{role}",
  "department": "{department}",
  
  "executive_summary": "A 3-4 sentence description of who this ideal candidate is and what they bring to the role.",
  
  "experience": {{
    "years": "X-Y years (e.g., 5-8 years)",
    "background": "Key industry/domain background and relevant experience",
    "ideal_companies": ["Type of company/industry 1", "Type of company/industry 2"]
  }},
  
  "must_have": [
    "Critical skill/competency 1 - why it matters",
    "Critical skill/competency 2 - why it matters",
    "Critical skill/competency 3 - why it matters",
    "Critical skill/competency 4 - why it matters"
  ],
  
  "nice_to_have": [
    "Bonus skill 1",
    "Bonus skill 2",
    "Bonus skill 3"
  ],
  
  "key_responsibilities": [
    "Primary responsibility 1 with scope",
    "Primary responsibility 2 with scope",
    "Primary responsibility 3 with scope",
    "Secondary responsibility 4"
  ],
  
  "success_metrics": {{
    "first_30_days": ["Milestone/deliverable 1", "Milestone/deliverable 2"],
    "first_90_days": ["Key achievement 1", "Key achievement 2"],
    "first_year": ["Strategic outcome 1", "Strategic outcome 2"]
  }},
  
  "team_fit": "Who do they work with? Team dynamics and collaboration style. 1-2 sentences.",
  
  "work_environment": {{
    "location": "On-site / Remote / Hybrid",
    "team_size": "Team size range (e.g., 5-10 people)",
    "pace": "Fast-paced / Structured / Balanced",
    "culture_values": ["Core value 1", "Core value 2", "Core value 3"]
  }},
  
  "personality_profile": "What type of person thrives? (e.g., analytical, creative, detail-oriented, strategic thinker, problem-solver)",
  
  "dealbreakers": [
    "Cannot compromise on this aspect",
    "This is non-negotiable"
  ],
  
  "ideal_candidate_portrait": "Final 2-3 sentence summary: The perfect candidate is..."
}}
"""


# =========================================================
# CLEANING UTILITIES
# =========================================================

def _strip_markdown(content: str) -> str:
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return content.strip()


def _remove_html(content: str) -> str:
    return re.sub(r"<[^>]+>", "", content)


def _normalize_whitespace(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def _clean_llm_output(content: str) -> str:
    content = _strip_markdown(content)
    content = _remove_html(content)
    content = _normalize_whitespace(content)
    return content


def _sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _recursive_sanitize(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _recursive_sanitize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_recursive_sanitize(i) for i in data]
    elif isinstance(data, str):
        return _sanitize_text(data)
    return data


# =========================================================
# STRUCTURE VALIDATION
# =========================================================

def _get_template(role: str, department: str) -> Dict[str, Any]:
    """Return base Ideal Candidate Profile template."""
    return {
        "role": role,
        "department": department,
        "executive_summary": "",
        "experience": {
            "years": "",
            "background": "",
            "ideal_companies": []
        },
        "must_have": [],
        "nice_to_have": [],
        "key_responsibilities": [],
        "success_metrics": {
            "first_30_days": [],
            "first_90_days": [],
            "first_year": []
        },
        "team_fit": "",
        "work_environment": {
            "location": "",
            "team_size": "",
            "pace": "",
            "culture_values": []
        },
        "personality_profile": "",
        "dealbreakers": [],
        "ideal_candidate_portrait": ""
    }


def _merge_template(template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in template.items():
        if key not in data:
            data[key] = value
        elif isinstance(value, dict):
            data[key] = _merge_template(value, data.get(key, {}))
    return data


# =========================================================
# MAIN BUILDER
# =========================================================

def build_profile(form_data: Dict, clarification_answers: List[Dict]) -> Dict:

    llm = get_llm()

    role = form_data.get("role", "Unknown Role")
    department = form_data.get("department", "General")

    prompt = JOB_PROFILE_PROMPT.format(
        role=role,
        department=department,
        form_data=json.dumps(form_data, indent=2),
        clarification_answers=json.dumps(clarification_answers, indent=2)
    )

    try:
        response = llm.invoke(prompt)
        content = response.content

        if isinstance(content, list):
            content = "".join(
                part.get("text", str(part))
                if isinstance(part, dict)
                else str(part)
                for part in content
            )

        content = _clean_llm_output(content)

        try:
            profile = json.loads(content)
        except json.JSONDecodeError:
            # Retry once
            retry_prompt = prompt + "\n\nYour previous output was invalid. Return ONLY valid JSON."
            retry_response = llm.invoke(retry_prompt)
            retry_content = _clean_llm_output(retry_response.content)
            profile = json.loads(retry_content)

        template = _get_template(role, department)
        profile = _merge_template(template, profile)
        profile = _recursive_sanitize(profile)

        return profile

    except Exception as e:
        print(f"[PROFILE_BUILDER ERROR] {e}")
        import traceback
        traceback.print_exc()
        
        # Build a reasonable fallback from form data
        template = _get_template(role, department)
        template["executive_summary"] = f"Seeking an experienced professional for {role} in {department} department"
        template["experience"]["years"] = form_data.get("experience", "3-5 years")
        template["experience"]["background"] = form_data.get("department", department)
        template["must_have"] = form_data.get("must_have_skills", "").split(",") if form_data.get("must_have_skills") else []
        template["nice_to_have"] = form_data.get("other_skills", "").split(",") if form_data.get("other_skills") else []
        template["work_environment"]["location"] = form_data.get("location", "")
        template["work_environment"]["team_size"] = form_data.get("team_size", "")
        template["ideal_candidate_portrait"] = f"A qualified professional ready to excel as {role}"
        return template


# =========================================================
# FREEFORM TEXT PARSER — Converts job posting/description to Ideal Candidate Profile
# =========================================================

PARSER_PROMPT = """
You are a senior HR strategist. Convert the following freeform job posting/description
into a structured "Ideal Candidate Profile" JSON.

RULES:
- Return STRICT valid JSON ONLY
- No markdown, no explanations
- Every field must exist (use "" for empty strings, [] for empty arrays)
- Extract data that is explicitly or implicitly mentioned
- Infer role and department from context

TEXT TO PARSE:
{profile_text}

Return this schema:

{{
  "role": "Job title inferred from text",
  "department": "Department inferred from text",
  "executive_summary": "2-3 sentence summary of the ideal candidate",
  "experience": {{
    "years": "Estimated years of experience (e.g., 5-8 years)",
    "background": "Industry/domain background mentioned",
    "ideal_companies": ["Type of company 1", "Type of company 2"]
  }},
  "must_have": [
    "Critical skill 1",
    "Critical skill 2",
    "Critical skill 3"
  ],
  "nice_to_have": [
    "Bonus skill 1",
    "Bonus skill 2"
  ],
  "key_responsibilities": [
    "Responsibility 1",
    "Responsibility 2",
    "Responsibility 3"
  ],
  "success_metrics": {{
    "first_30_days": ["Onboard and learn", "Meet key teams"],
    "first_90_days": ["Deliver first project", "Establish rhythm"],
    "first_year": ["Strategic impact", "Team leadership"]
  }},
  "team_fit": "Team size and dynamics description",
  "work_environment": {{
    "location": "Location mode (On-site/Remote/Hybrid)",
    "team_size": "Team size (e.g., 5-10 people)",
    "pace": "Work pace (Fast-paced/Balanced/Structured)",
    "culture_values": ["Collaboration", "Innovation", "Integrity"]
  }},
  "personality_profile": "Ideal candidate characteristics",
  "dealbreakers": ["List any hard requirements"],
  "ideal_candidate_portrait": "2-3 sentence portrait of ideal fit"
}}
"""


def parse_profile_text(profile_text: str) -> Dict:
    """Parse freeform job posting/profile text into Ideal Candidate Profile JSON."""
    llm = get_llm()
    prompt = PARSER_PROMPT.format(profile_text=profile_text[:4000])
    
    try:
        response = llm.invoke(prompt)
        content = _clean_llm_output(response.content)
        profile = json.loads(content)
        
        # Merge with template to ensure all fields exist
        template = _get_template(
            profile.get("role", "Unknown"),
            profile.get("department", "General")
        )
        profile = _merge_template(template, profile)
        profile = _recursive_sanitize(profile)
        return profile

    except Exception as e:
        print(f"[PROFILE_PARSER ERROR] {e}")
        # Return minimal template fallback
        return _get_template("Unknown Role", "General")


# Alias for backward compatibility
def parse_job_profile_text(profile_text: str) -> Dict:
    """Alias for parse_profile_text for backward compatibility."""
    return parse_profile_text(profile_text)