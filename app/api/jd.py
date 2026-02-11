# app/api/jd.py

from fastapi import APIRouter
from app.agents.jd_generator import generate_jd
from app.agents.jd_clarifier import generate_clarifying_questions
from app.agents.jd_chatbot import refine_jd
from app.agents.profile_builder import build_profile
import json

router = APIRouter(
    prefix="/jd",
    tags=["Job Description"]
)

@router.post("/clarify")
def clarify_jd_api(payload: dict):
    """Agent 1: Generate clarifying questions from form data (no draft needed)."""
    questions = generate_clarifying_questions(form_data=payload)

    if isinstance(questions, str):
        questions = json.loads(questions)

    return {"questions": questions}


@router.post("/profile")
def profile_builder_api(payload: dict):
    """Agent 2: Build ideal candidate profile."""
    profile = build_profile(
        form_data=payload.get("form_data", {}),
        clarification_answers=payload.get("answers", [])
    )
    return {"profile": profile}


@router.post("/generate")
def generate_jd_api(payload: dict):
    """Agent 3: Generate JD from profile + form data."""
    jd = generate_jd(
        form_data=payload.get("form_data", payload),
        profile=payload.get("profile", None)
    )
    return {"jd": jd}


@router.post("/refine")
def refine_jd_api(payload: dict):
    """Agent 4: Refine JD based on user instruction."""
    updated_jd = refine_jd(
        current_jd=payload["jd"],
        instruction=payload["instruction"],
        role=payload.get("role", ""),
        session_id=payload.get("session_id", "")
    )
    return {"jd": updated_jd}
