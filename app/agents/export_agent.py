#export_agent
# export candidate ranking to excel for easy sharing and analysis. This agent takes the final ranked candidates and their scores, and generates an Excel file with all relevant information. The file can include candidate names, scores, key skills, and any other relevant data points that would be useful for recruiters to review and share with hiring teams.
import pandas as pd
import os
import shutil

def export_agent(state):
    os.makedirs("exports", exist_ok=True)
    os.makedirs(os.path.join("exports", "resumes"), exist_ok=True)

    ranking = state.get("ranking", [])

    # copy resumes (if present in parsed_resumes)
    parsed_resumes = state.get("parsed_resumes", [])
    resume_map = {r.get("candidate_id"): r.get("resume_path") for r in parsed_resumes}

    # attach resume_export_path to ranking entries
    for r in ranking:
        cid = r.get("candidate_id")
        src = resume_map.get(cid)
        if src and os.path.exists(src):
            dest = os.path.join("exports", "resumes", os.path.basename(src))
            try:
                shutil.copy(src, dest)
                r["resume_export_path"] = dest
            except Exception:
                r["resume_export_path"] = None
        else:
            r["resume_export_path"] = None

    df = pd.DataFrame(ranking)
    path = "exports/candidate_ranking.xlsx"
    df.to_excel(path, index=False)

    # set export path in state so API response can return it
    state["export_path"] = path
    return state
