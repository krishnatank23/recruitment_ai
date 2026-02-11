#job fit evaluator
from typing import Dict, List
from app.utils.llm import get_llm


# -----------------------------
# Scoring weights (tunable)
# -----------------------------
WEIGHTS = {
    "semantic": 0.4,
    "skills": 0.35,
    "experience": 0.25
}


def job_fit_evaluator(state: Dict) -> Dict:
    """
    Converts semantic similarity + rules into actual JOB FIT %
    """

    parsed_jd = state["parsed_jd"]
    parsed_resumes = state["parsed_resumes"]
    semantic_results = {
        r["candidate_id"]: r for r in state["semantic_scores"]
    }

    llm = get_llm()
    results = []

    jd_skills = set(parsed_jd.get("must_have_skills", []))
    jd_exp = parsed_jd.get("experience_years", 0)

    for resume in parsed_resumes:
        cid = resume["candidate_id"]
        resume_skills = set(resume.get("skills", []))
        resume_exp = resume.get("experience_years", 0)
        semantic_score = semantic_results.get(cid, {}).get("semantic_score", 0)

        # -----------------------------
        # HARD REJECTION
        # -----------------------------
        missing_skills = jd_skills - resume_skills
        if missing_skills:
            results.append({
                "candidate_id": cid,
                "decision": "REJECT",
                "job_fit_percent": 0,
                "final_score": 0,
                "strengths": [],
                "gaps": list(missing_skills),
                "reason": "Missing core skills"
            })
            continue

        # -----------------------------
        # SCORING
        # -----------------------------
        skill_match = len(jd_skills & resume_skills) / max(len(jd_skills), 1)
        experience_match = min(resume_exp / max(jd_exp, 1), 1)

        final_score = (
            semantic_score * WEIGHTS["semantic"]
            + skill_match * WEIGHTS["skills"]
            + experience_match * WEIGHTS["experience"]
        )

        job_fit_percent = round(final_score * 100)

        # -----------------------------
        # EXPLANATION (LLM)
        # -----------------------------
        prompt = f"""
        Job required skills: {list(jd_skills)}
        Resume skills: {list(resume_skills)}
        Resume experience: {resume_exp} years

        Return STRICT JSON only:
        {{
          "strengths": [],
          "gaps": []
        }}
        """

        try:
            response = llm.invoke(prompt)
            response = response.strip().replace("```json", "").replace("```", "")
            explanation = eval(response)
        except Exception:
            explanation = {"strengths": [], "gaps": []}

        results.append({
            "candidate_id": cid,
            "decision": "ACCEPT",
            "job_fit_percent": job_fit_percent,
            "final_score": final_score,
            "semantic_score": semantic_score,
            "skill_match": skill_match,
            "experience_match": experience_match,
            "strengths": explanation["strengths"],
            "gaps": explanation["gaps"]
        })

    state["job_fit_results"] = results
    return state
