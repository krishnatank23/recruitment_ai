# persona_builder.py - Generate role-specific candidate personas from profile
import json
import re
from app.utils.llm import get_llm

PERSONA_PROMPT = """
You are a senior hiring strategist.

You are given an Ideal Candidate Profile for a role.

Your task is to create 5 DISTINCT ideal candidate personas - each representing a DIFFERENT type of person who could succeed in this role.

These personas will later be used to evaluate real candidate CVs, so they must be specific and actionable.

INPUT:
-----------------------------
IDEAL CANDIDATE PROFILE:
{profile_text}
-----------------------------

OUTPUT FORMAT (STRICT JSON ARRAY):
[
  {{
    "persona_id": "P1",
    "name": "Short Persona Title (e.g. 'The Scalable Systems Expert')",
    "summary": "2-3 sentence description of who this persona is and why they'd succeed",
    "experience_range": "X-Y years",
    "core_strengths": [
      "Strength 1: why it matters for this role",
      "Strength 2: why it matters for this role",
      "Strength 3: why it matters for this role"
    ],
    "required_skills": ["Skill 1", "Skill 2", "Skill 3"],
    "nice_to_have_skills": ["Skill 1", "Skill 2"],
    "behavioral_traits": [
      "Trait 1: why it's relevant",
      "Trait 2: why it's relevant"
    ],
    "red_flags": [
      "Warning sign 1 that would disqualify this persona type",
      "Warning sign 2"
    ],
    "success_definition": "What does success look like for this persona in 6 months?"
  }}
]

RULES:
- Create 5 personas. Each must represent a DIFFERENT hiring path.
- Use ONLY information from the given profile. Do NOT hallucinate.
- Each persona should have different experience ranges and strengths.
- Output ONLY valid JSON array. No markdown, no explanations, no wrapping.
"""


def _extract_keywords(text: str) -> set:
    """Extract simple keywords for relevance checks."""
    if not text:
        return set()
    stop_words = {
        "the", "and", "for", "with", "from", "this", "that", "will", "have",
        "must", "role", "job", "candidate", "years", "year", "experience",
        "skills", "skill", "work", "team", "ability", "strong", "good",
        "using", "based", "need", "required", "preferred", "plus"
    }
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{2,}", text.lower())
    return {t for t in tokens if t not in stop_words}


def _personas_text(personas: list) -> str:
    """Flatten persona fields into a single text block."""
    parts = []
    for persona in personas or []:
        parts.extend([
            str(persona.get("name", "")),
            str(persona.get("summary", "")),
            str(persona.get("experience_range", "")),
            str(persona.get("success_definition", "")),
            " ".join(persona.get("core_strengths", []) or []),
            " ".join(persona.get("required_skills", []) or []),
            " ".join(persona.get("nice_to_have_skills", []) or []),
            " ".join(persona.get("behavioral_traits", []) or []),
            " ".join(persona.get("red_flags", []) or []),
        ])
    return " ".join(parts)


def _is_profile_aligned(profile_text: str, personas: list) -> bool:
    """Basic relevance check between profile and generated personas."""
    profile_keywords = _extract_keywords(profile_text)
    persona_keywords = _extract_keywords(_personas_text(personas))
    if not profile_keywords or not persona_keywords:
        return False

    overlap = profile_keywords.intersection(persona_keywords)
    min_overlap = min(6, max(3, len(profile_keywords) // 12))
    return len(overlap) >= min_overlap


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    s = str(value).strip()
    return [s] if s else []


def _normalize_persona(persona: dict, index: int) -> dict:
    """Normalize persona to strict schema and keep legacy aliases for matcher compatibility."""
    normalized = {
        "persona_id": str(persona.get("persona_id") or f"P{index}"),
        "name": str(persona.get("name") or f"Persona {index}").strip(),
        "summary": str(persona.get("summary") or persona.get("background") or "").strip(),
        "experience_range": str(persona.get("experience_range") or persona.get("experience_level") or "").strip(),
        "core_strengths": _as_list(persona.get("core_strengths") or persona.get("key_strengths")),
        "required_skills": _as_list(persona.get("required_skills") or persona.get("must_have_skills")),
        "nice_to_have_skills": _as_list(persona.get("nice_to_have_skills") or persona.get("nice_to_have")),
        "behavioral_traits": _as_list(persona.get("behavioral_traits")),
        "red_flags": _as_list(persona.get("red_flags")),
        "success_definition": str(persona.get("success_definition") or persona.get("ideal_for") or "").strip(),
    }

    # Legacy aliases used by existing candidate_matcher.py
    normalized["background"] = normalized["summary"]
    normalized["key_strengths"] = normalized["core_strengths"]
    normalized["experience_level"] = normalized["experience_range"]
    normalized["must_have_skills"] = normalized["required_skills"]
    normalized["nice_to_have"] = normalized["nice_to_have_skills"]
    normalized["ideal_for"] = normalized["success_definition"]

    return normalized


def _parse_personas(response_text: str) -> list:
    """Parse personas from strict JSON array or wrapped object."""
    text = response_text.strip()

    if "```json" in text:
        json_start = text.find("```json") + 7
        json_end = text.find("```", json_start)
        text = text[json_start:json_end].strip()

    if text.startswith("["):
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []

    if "{" in text and "}" in text:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        obj = json.loads(text[json_start:json_end])
        if isinstance(obj, dict):
            personas = obj.get("personas", [])
            return personas if isinstance(personas, list) else []

    parsed = json.loads(text)
    return parsed if isinstance(parsed, list) else []


def generate_personas(profile_text: str) -> dict:
    """
    Generate 3-5 personas from an ideal candidate profile using LLM.

    Args:
        profile_text: Ideal candidate profile text

    Returns:
        dict with personas list and metadata
    """
    try:
        llm = get_llm()

        print("[PERSONA_BUILDER] Generating personas from profile...")
        base_prompt = PERSONA_PROMPT.format(profile_text=profile_text)
        attempts = [
            base_prompt,
            base_prompt + "\n\nRe-check and ensure personas are strictly tied to the provided job profile.",
        ]

        last_error = None
        for attempt_idx, prompt in enumerate(attempts, start=1):
            print(f"[PERSONA_BUILDER] Attempt {attempt_idx}...")
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, "content") else str(response)
            print("[PERSONA_BUILDER] LLM response received")

            try:
                personas_raw = _parse_personas(response_text)
                personas = [_normalize_persona(p, i + 1) for i, p in enumerate(personas_raw)]
                count = len(personas)

                if count < 3 or count > 5:
                    last_error = f"Expected 3-5 personas, got {count}"
                    print(f"[PERSONA_BUILDER] {last_error}")
                    continue

                if not _is_profile_aligned(profile_text, personas):
                    last_error = "Generated personas are not sufficiently aligned with the job profile."
                    print(f"[PERSONA_BUILDER] {last_error}")
                    continue

                print(f"[PERSONA_BUILDER] Successfully created {count} profile-aligned personas")
                return {
                    "success": True,
                    "personas": personas,
                    "count": count,
                }

            except json.JSONDecodeError as e:
                last_error = f"Failed to parse personas JSON: {str(e)}"
                print(f"[PERSONA_BUILDER] JSON parsing error: {e}")
                print(f"[PERSONA_BUILDER] Response text: {response_text[:200]}...")

        return {
            "success": False,
            "error": last_error or "Failed to generate valid personas.",
            "personas": [],
            "count": 0,
        }

    except Exception as e:
        print(f"[PERSONA_BUILDER] Error generating personas: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "personas": [],
            "count": 0,
        }


def get_persona_template() -> dict:
    """Return a template persona for fallback."""
    return {
        "persona_id": "P1",
        "name": "Ideal Candidate",
        "summary": "Experienced professional aligned to the role profile.",
        "experience_range": "3-6 years",
        "core_strengths": ["Role-relevant strength 1", "Role-relevant strength 2", "Role-relevant strength 3"],
        "required_skills": ["Required skill 1", "Required skill 2", "Required skill 3"],
        "nice_to_have_skills": ["Nice to have skill 1", "Nice to have skill 2"],
        "behavioral_traits": ["Ownership", "Collaboration"],
        "red_flags": ["Cannot demonstrate required skill depth", "Poor role-relevant communication"],
        "success_definition": "Delivers role-critical outcomes within 6 months.",
    }
