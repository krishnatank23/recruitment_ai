from typing import Dict, List
from app.db.vector_store import VectorStore


def semantic_matcher(state: Dict) -> Dict:
    """
    LangGraph node:
    - Takes parsed JD + parsed resumes
    - Computes semantic similarity per resume
    - Stores results in state["semantic_scores"]
    """

    # ----------------------------
    # Read from state (STRICT)
    # ----------------------------
    parsed_jd = state.get("parsed_jd", {})
    parsed_resumes = state.get("parsed_resumes", [])

    jd_role = parsed_jd.get("role", "")
    jd_responsibilities = " ".join(parsed_jd.get("responsibilities", []))
    jd_skills = " ".join(parsed_jd.get("must_have_skills", []))

    semantic_results: List[Dict] = []

    # ----------------------------
    # Process each resume
    # ----------------------------
    for resume in parsed_resumes:
        candidate_id = resume.get("candidate_id")

        store = VectorStore()

        # ----------------------------
        # Add resume sections to vector store
        # ----------------------------
        texts = [
            resume.get("summary", ""),
            resume.get("experience", ""),
            resume.get("projects", ""),
            " ".join(resume.get("skills", [])),
        ]

        metadatas = [
            {"candidate_id": candidate_id, "section": "summary"},
            {"candidate_id": candidate_id, "section": "experience"},
            {"candidate_id": candidate_id, "section": "projects"},
            {"candidate_id": candidate_id, "section": "skills"},
        ]

        store.add(texts, metadatas)

        # ----------------------------
        # Query with JD context
        # ----------------------------
        queries = {
            "summary": jd_role,
            "experience": jd_responsibilities,
            "skills": jd_skills,
        }

        section_scores = {}

        for section, query in queries.items():
            if not query.strip():
                section_scores[section] = 0.0
                continue

            matches = store.search(query, k=2)

            if not matches:
                section_scores[section] = 0.0
            else:
                section_scores[section] = round(
                    sum(score for _, score in matches) / len(matches),
                    3
                )

        # ----------------------------
        # Final weighted semantic score
        # ----------------------------
        final_semantic_score = round(
            0.4 * section_scores.get("experience", 0.0)
            + 0.4 * section_scores.get("skills", 0.0)
            + 0.2 * section_scores.get("summary", 0.0),
            3
        )

        semantic_results.append({
            "candidate_id": candidate_id,
            "semantic_score": final_semantic_score,
            "section_scores": section_scores
        })

    # ----------------------------
    # Write back to state
    # ----------------------------
    state["semantic_scores"] = semantic_results
    return state
