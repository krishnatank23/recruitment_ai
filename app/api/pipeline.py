#pipeline.py
from fastapi import APIRouter, UploadFile, File
import tempfile
import os
import shutil

from app.graphs.recruitment_graph import build_recruitment_graph
from app.utils.text_cleanup import extract_text_from_file

router = APIRouter()


@router.post("/run_pipeline")
async def run_pipeline(
    jd_file: UploadFile = File(...),
    resumes: UploadFile = File(...)
):
    """
    Accepts:
    - JD file (PDF / DOCX / TXT)
    - Resumes (ZIP / PDF / DOCX)

    Returns:
    - Ranked candidates
    - Resume paths
    - Excel export path
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        # -----------------------------
        # SAVE JD FILE
        # -----------------------------
        jd_path = os.path.join(temp_dir, jd_file.filename)
        with open(jd_path, "wb") as f:
            shutil.copyfileobj(jd_file.file, f)

        jd_text = extract_text_from_file(jd_path)

        # -----------------------------
        # SAVE RESUME FILE
        # -----------------------------
        resume_path = os.path.join(temp_dir, resumes.filename)
        with open(resume_path, "wb") as f:
            shutil.copyfileobj(resumes.file, f)

        # -----------------------------
        # INITIAL STATE FOR LANGGRAPH
        # -----------------------------
        state = {
            "jd_text": jd_text,
            "resume_files": [resume_path]
        }

        # -----------------------------
        # RUN LANGGRAPH
        # -----------------------------
        graph = build_recruitment_graph()
        final_state = graph.invoke(state)

        # -----------------------------
        # RESPONSE FOR STREAMLIT
        # -----------------------------
        return {
            "ranking": final_state.get("ranking", []),
            "export_path": final_state.get("export_path")
        }
