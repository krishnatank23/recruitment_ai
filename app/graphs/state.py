#state.py
from typing import TypedDict, List, Dict, Any


class RecruitmentState(TypedDict):
    jd_text: str
    resume_files: List[str]

    parsed_jd: Dict[str, Any]
    parsed_resumes: List[Dict[str, Any]]

    semantic_scores: List[Dict[str, Any]]
    job_fit_results: List[Dict[str, Any]]

    ranking: List[Dict[str, Any]]
    export_path: str
