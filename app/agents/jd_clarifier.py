# app/agents/jd_clarifier.py
# Agent 1: Clarifying Questions Generator
# Generates adaptive MCQs from full Google Form ground truth

from app.utils.llm import get_llm
import json
import re

CLARIFY_PROMPT = """You are a senior recruitment strategist.

SCENARIO:
The Head of {department} has requested to hire a {title}.
Your job is to ask clarifying questions that uncover the real hiring intent.

GROUND TRUTH (GOOGLE FORM DATA):
{form_data_json}

TASK:
Generate exactly 5 multiple-choice questions that:
1. Are tailored to this exact role, department, and form context.
2. Cover different themes (scope, outcomes, ownership, collaboration, priorities, capability depth).
3. Are not repetitive in structure or meaning.
4. Each question has exactly 4 options.
5. Options are specific to this role and support multi-select.

OUTPUT FORMAT (STRICT JSON ARRAY ONLY):
[
  {{
    "id": "q1",
    "question": "...",
    "options": ["Option A", "Option B", "Option C", "Option D"]
  }},
  {{
    "id": "q2",
    "question": "...",
    "options": ["Option A", "Option B", "Option C", "Option D"]
  }},
  {{
    "id": "q3",
    "question": "...",
    "options": ["Option A", "Option B", "Option C", "Option D"]
  }},
  {{
    "id": "q4",
    "question": "...",
    "options": ["Option A", "Option B", "Option C", "Option D"]
  }},
  {{
    "id": "q5",
    "question": "...",
    "options": ["Option A", "Option B", "Option C", "Option D"]
  }}
]

RULES:
- Use Google Form data as ground truth.
- Do not ask role-generic questions if role-specific context exists.
- Do not ask about salary, CTC, compensation, work mode, remote/hybrid, travel, shift timing, or urgency.
- Output only a valid JSON array. No markdown. No explanation.
"""

BANNED_KEYWORDS = [
    "salary", "ctc", "compensation",
    "work mode", "remote", "hybrid", "onsite",
    "travel", "shift", "timing", "working hours",
    "urgency", "how urgent"
]


def _extract_json(text: str) -> str:
    """Extract JSON array from LLM response."""
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end].strip()

    match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if match:
        return match.group(0)

    return text.strip()


def _is_valid_question(q: dict) -> bool:
    """Validate question structure."""
    if not isinstance(q, dict):
        return False
    required = {"id", "question", "options"}
    if not required.issubset(q.keys()):
        return False
    if not isinstance(q.get("options"), list) or len(q["options"]) != 4:
        return False
    if not isinstance(q.get("question"), str) or not q["question"].strip():
        return False
    return True


def post_validate_questions(questions: list) -> list:
    """Filter banned and duplicate/near-duplicate questions."""
    valid = []
    seen = set()

    for q in questions:
        question_text = str(q.get("question", "")).strip()
        question_lower = question_text.lower()

        if any(b.lower() in question_lower for b in BANNED_KEYWORDS):
            continue

        options = q.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            continue

        # Avoid duplicate/near-duplicate questions
        norm = re.sub(r"[^a-z0-9]+", " ", question_lower).strip()
        if norm in seen:
            continue
        seen.add(norm)

        # Normalize id format
        q["id"] = f"q{len(valid) + 1}"
        q["question"] = question_text
        q["options"] = [str(o).strip() for o in options]
        valid.append(q)

    return valid


def generate_clarifying_questions(form_data: dict) -> list:
    """
    Generate 5 clarifying questions dynamically from Google Form data.

    Args:
        form_data: dict from Google Form containing role/department and all fields.

    Returns:
        List of 5 MCQ questions with 4 options each.
    """
    llm = get_llm()

    title = form_data.get("role", "Unknown Role")
    department = form_data.get("department", "General")
    form_data_json = json.dumps(form_data, indent=2)

    prompt = CLARIFY_PROMPT.format(
        title=title,
        department=department,
        form_data_json=form_data_json,
    )

    try:
        response = llm.invoke(prompt)
        raw_text = str(response.content)
    except Exception as e:
        print(f"[JD_CLARIFIER] Error calling LLM: {e}")
        return []

    try:
        json_text = _extract_json(raw_text)
        questions = json.loads(json_text)
    except Exception as e:
        print(f"[JD_CLARIFIER] JSON parse error: {e}")
        return []

    if not isinstance(questions, list):
        return []

    questions = [q for q in questions if _is_valid_question(q)]
    questions = post_validate_questions(questions)

    # Enforce exactly 5 questions for current UI flow
    return questions[:5]


if __name__ == "__main__":
    from app.utils.google_form_loader import fetch_google_form_data

    rows = fetch_google_form_data()
    if not rows:
        print("No Google Form data found.")
        raise SystemExit(1)

    selected = rows[0]
    questions = generate_clarifying_questions(form_data=selected)

    print(f"\nGenerated {len(questions)} questions for {selected.get('role', '')} ({selected.get('department', '')})\n")
    for q in questions:
        print(f"{q['id']}: {q['question']}")
        for i, opt in enumerate(q["options"], start=1):
            print(f"  {i}. {opt}")
        print("")
