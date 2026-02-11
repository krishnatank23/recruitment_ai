# def score_candidate(jd_embedding, resume_embedding):
#     # here we just reuse cosine similarity
#     # can add weights for keywords match, experience, location, etc.
#     from app.agents.semantic_matcher import compute_similarity
#     return compute_similarity(jd_embedding, resume_embedding)
def score_candidate(jd, resume, semantic_score):
    skill_overlap = len(
        set(jd["required_skills"]) &
        set(resume["sections"]["skills"].split())
    )

    skill_score = skill_overlap / max(len(jd["required_skills"]), 1)

    experience_score = 1.0
    if jd["min_experience"]:
        experience_score = 0.8  # heuristic (can improve)

    final_score = (
        0.5 * semantic_score +
        0.3 * skill_score +
        0.2 * experience_score
    )

    return {
        "final_score": round(final_score, 3),
        "breakdown": {
            "semantic": semantic_score,
            "skill_match": skill_score,
            "experience": experience_score
        }
    }

def scoring_agent(state):
    results = {}

    for cid, data in state["semantic_scores"].items():
        semantic = data["semantic_score"]
        gap = 1 - semantic

        final_score = round(semantic * 100, 2)

        explanation = (
            "Strong role alignment"
            if semantic > 0.8
            else "Partial role alignment with skill gaps"
        )

        results[cid] = {
            "final_score": final_score,
            "semantic_score": semantic,
            "gap_score": round(gap, 2),
            "explanation": explanation
        }

    return {"scoring": results}
