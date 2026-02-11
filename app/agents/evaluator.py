#evaluator.py
from app.agents.scoring import score_candidate

def evaluate_candidates(jd_embedding, matched_resumes, resume_embeddings):
    eval_list = []
    for candidate, emb in zip(matched_resumes, resume_embeddings):
        score = score_candidate(jd_embedding, emb)
        candidate["final_score"] = score
        eval_list.append(candidate)
    return sorted(eval_list, key=lambda x: x["final_score"], reverse=True)
