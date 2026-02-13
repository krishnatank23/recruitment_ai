# candidate_matcher.py - Match resumes to personas using LLM scoring
import json
from app.utils.llm import get_llm

MATCHING_PROMPT = """
You are an expert recruiter evaluating how well a candidate matches a specific persona for a job role.

PERSONA DESCRIPTION:
{persona_description}

CANDIDATE RESUME:
{resume_text}

Evaluate if this candidate matches the persona on a scale of 0-100%.

Return ONLY a valid JSON object (no other text):
{{
  "match_score": <0-100>,
  "match_percentage": "<score>%",
  "key_strengths_match": ["strength 1 that matches persona", "strength 2", "strength 3"],
  "gaps": ["gap 1 if exists", "gap 2 if exists"],
  "reasoning": "2-3 sentences explaining the match score",
  "verdict": "Strong Match / Good Match / Moderate Match / Weak Match / Not a Match"
}}

Requirements:
- match_score must be a number 0-100
- Be objective and fair in evaluation
- Consider both explicit and implicit qualifications
- Return ONLY valid JSON
"""

def match_resume_to_persona(resume_text: str, persona: dict) -> dict:
    """
    Match a single resume to a persona using LLM.
    
    Args:
        resume_text: Candidate resume text
        persona: Persona dict with name, description, etc.
        
    Returns:
        dict with match_score, reasoning, etc.
    """
    try:
        llm = get_llm()
        
        persona_name = persona.get("name", "Unknown")
        print(f"[CANDIDATE_MATCHER] Matching resume to persona: {persona_name}")
        
        # Format persona description
        persona_desc = f"""
NAME: {persona.get('name', 'N/A')}
BACKGROUND: {persona.get('background', 'N/A')}
KEY STRENGTHS: {', '.join(persona.get('key_strengths', []))}
EXPERIENCE LEVEL: {persona.get('experience_level', 'N/A')}
MUST-HAVE SKILLS: {', '.join(persona.get('must_have_skills', []))}
NICE-TO-HAVE: {', '.join(persona.get('nice_to_have', []))}
IDEAL FOR: {persona.get('ideal_for', 'N/A')}
RED FLAGS: {persona.get('red_flags', 'N/A')}
"""
        
        # Build prompt
        prompt = MATCHING_PROMPT.format(
            persona_description=persona_desc,
            resume_text=resume_text[:3000]  # Limit resume text
        )
        
        # Call LLM
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        print(f"[CANDIDATE_MATCHER] LLM evaluation complete")
        
        # Parse JSON response
        try:
            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
            else:
                json_str = response_text
            
            result = json.loads(json_str)
            result["success"] = True
            result["persona_name"] = persona_name
            return result
            
        except json.JSONDecodeError as e:
            print(f"[CANDIDATE_MATCHER] JSON parse error: {e}")
            
            # Fallback result
            return {
                "success": False,
                "error": f"Failed to parse match result: {str(e)}",
                "match_score": 0,
                "match_percentage": "0%",
                "persona_name": persona_name,
                "reasoning": "Evaluation error occurred"
            }
            
    except Exception as e:
        print(f"[CANDIDATE_MATCHER] Error matching resume: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "match_score": 0,
            "match_percentage": "0%",
            "persona_name": persona.get("name", "Unknown"),
            "reasoning": "Error occurred during evaluation"
        }

def match_candidates_to_personas(candidates: list, personas: list) -> dict:
    """
    Match all candidates to all personas.
    
    Args:
        candidates: List of candidate dicts with resume_text
        personas: List of persona dicts
        
    Returns:
        dict with results matrix
    """
    try:
        print(f"[CANDIDATE_MATCHER] Starting matching: {len(candidates)} candidates vs {len(personas)} personas")
        
        results = {
            "success": True,
            "total_candidates": len(candidates),
            "total_personas": len(personas),
            "matches": []
        }
        
        # Match each candidate to each persona
        for candidate in candidates:
            candidate_name = candidate.get("name", f"Candidate {len(results['matches']) + 1}")
            candidate_resume = candidate.get("resume_text", "")
            
            if not candidate_resume.strip():
                print(f"[CANDIDATE_MATCHER] Skipping {candidate_name} - empty resume")
                continue
            
            candidate_matches = {
                "candidate_name": candidate_name,
                "persona_matches": []
            }
            
            # Match to each persona
            for persona in personas:
                match_result = match_resume_to_persona(candidate_resume, persona)
                
                candidate_matches["persona_matches"].append({
                    "persona_name": persona.get("name", "Unknown"),
                    "persona_id": persona.get("persona_id", 0),
                    **match_result
                })
            
            results["matches"].append(candidate_matches)
        
        print(f"[CANDIDATE_MATCHER] Completed matching for {len(results['matches'])} candidates")
        return results
        
    except Exception as e:
        print(f"[CANDIDATE_MATCHER] Error in matching: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "matches": []
        }

def get_best_matches(match_results: dict, top_n: int = 5) -> list:
    """
    Get top personized matches for each persona.
    
    Args:
        match_results: Results from match_candidates_to_personas
        top_n: Number of top candidates per persona
        
    Returns:
        List of top matches organized by persona
    """
    try:
        top_matches = {}
        
        # Collect all scores by persona
        for candidate in match_results.get("matches", []):
            for match in candidate.get("persona_matches", []):
                persona_name = match.get("persona_name", "Unknown")
                
                if persona_name not in top_matches:
                    top_matches[persona_name] = []
                
                top_matches[persona_name].append({
                    "candidate_name": candidate.get("candidate_name"),
                    "score": match.get("match_score", 0),
                    "percentage": match.get("match_percentage", "0%"),
                    "reasoning": match.get("reasoning", ""),
                    "verdict": match.get("verdict", "Unknown"),
                    "strengths": match.get("key_strengths_match", []),
                    "gaps": match.get("gaps", [])
                })
        
        # Sort and get top N for each persona
        result = {}
        for persona_name, matches in top_matches.items():
            sorted_matches = sorted(matches, key=lambda x: x["score"], reverse=True)
            result[persona_name] = sorted_matches[:top_n]
        
        return result
        
    except Exception as e:
        print(f"[CANDIDATE_MATCHER] Error getting best matches: {e}")
        return {}
