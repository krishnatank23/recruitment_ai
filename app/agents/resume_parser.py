# resume_parser.py - Extract text from resume files (PDF, DOCX, TXT, ZIP)
import os
import zipfile
from typing import Dict, List
from pathlib import Path

SUPPORTED_EXT = (".pdf", ".doc", ".docx", ".txt")

def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        print(f"[RESUME_PARSER] Extracted {len(text)} chars from PDF: {os.path.basename(file_path)}")
        return text
    except Exception as e:
        print(f"[RESUME_PARSER] Error extracting PDF: {e}")
        return ""

def _extract_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        print(f"[RESUME_PARSER] Extracted {len(text)} chars from DOCX: {os.path.basename(file_path)}")
        return text
    except Exception as e:
        print(f"[RESUME_PARSER] Error extracting DOCX: {e}")
        return ""

def _extract_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        print(f"[RESUME_PARSER] Extracted {len(text)} chars from TXT: {os.path.basename(file_path)}")
        return text
    except Exception as e:
        print(f"[RESUME_PARSER] Error extracting TXT: {e}")
        return ""

def extract_resume_text(file_path: str) -> str:
    """Extract text from resume file (PDF, DOCX, TXT)."""
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        return _extract_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        return _extract_docx(file_path)
    elif file_ext == '.txt':
        return _extract_txt(file_path)
    else:
        print(f"[RESUME_PARSER] Unsupported file format: {file_ext}")
        return ""

def _extract_resumes_from_files(resume_files: List[str]) -> List[Dict]:
    """
    Takes list of file paths (zip or single resume),
    returns list of {file, path, text}
    """
    extracted = []

    for path in resume_files:
        # Handle ZIP files
        if path.lower().endswith(".zip"):
            print(f"[RESUME_PARSER] Extracting ZIP: {os.path.basename(path)}")
            extract_dir = path + "_unzipped"
            os.makedirs(extract_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(path, "r") as z:
                    z.extractall(extract_dir)

                for root, _, files in os.walk(extract_dir):
                    for f in files:
                        if f.lower().endswith(SUPPORTED_EXT):
                            full_path = os.path.join(root, f)
                            text = extract_resume_text(full_path)
                            if text.strip():
                                extracted.append({
                                    "file": f,
                                    "path": full_path,
                                    "text": text
                                })
            except Exception as e:
                print(f"[RESUME_PARSER] Error extracting ZIP: {e}")
        
        # Handle single files
        else:
            if path.lower().endswith(SUPPORTED_EXT):
                text = extract_resume_text(path)
                if text.strip():
                    extracted.append({
                        "file": os.path.basename(path),
                        "path": path,
                        "text": text
                    })

    return extracted


def parse_multiple_resumes(file_paths: list) -> list:
    """
    Parse multiple resume files.
    
    Args:
        file_paths: List of file paths
        
    Returns:
        List of dicts with {filename, text, character_count, success}
    """
    raw_resumes = _extract_resumes_from_files(file_paths)
    
    print(f"[RESUME_PARSER] Processing {len(raw_resumes)} parsed resumes...")
    
    return raw_resumes

def parse_candidate_resumes(resume_files: List[str]) -> Dict:
    """
    Parse candidate resumes using extract_resume_text.
    Returns structured data for candidate matching.
    """
    try:
        parsed_resumes = parse_multiple_resumes(resume_files)
        
        candidate_data = {
            "success": True,
            "candidates": [],
            "total": len(parsed_resumes)
        }
        
        for i, resume in enumerate(parsed_resumes, 1):
            candidate_data["candidates"].append({
                "candidate_id": i,
                "name": resume.get("file", f"Candidate {i}"),
                "resume_text": resume.get("text", ""),
                "file_path": resume.get("path", "")
            })
        
        print(f"[RESUME_PARSER] Successfully parsed {len(parsed_resumes)} resumes")
        return candidate_data
        
    except Exception as e:
        print(f"[RESUME_PARSER] Error parsing resumes: {e}")
        return {
            "success": False,
            "error": str(e),
            "candidates": [],
            "total": 0
        }


def resume_parser(state: Dict) -> Dict:
    """
    LangGraph node (legacy support):
    - Reads resume_files
    - Extracts raw resume text
    - Parses into structured resumes
    - Writes state["parsed_resumes"]
    """
    resume_files = state.get("resume_files", [])
    
    raw_resumes = _extract_resumes_from_files(resume_files)
    
    parsed_resumes = []
    for r in raw_resumes:
        parsed_resumes.append({
            "candidate_id": r["file"],
            "raw_text": r["text"],
            "resume_path": r["path"]
        })
    
    state["parsed_resumes"] = parsed_resumes
    return state
