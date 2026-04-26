import re
from .jd_parser import SKILLS_CONFIG

def analyze_resume(resume_text: str) -> list[str]:
    """
    Parses a Candidate Resume and extracts claimed skills using alias config.
    Returns a list of string skills.
    """
    resume_lower = resume_text.lower()
    claimed_skills = []
    
    for main_skill, skill_data in SKILLS_CONFIG.items():
        aliases = skill_data.get("aliases", [])
        matched = False
        for alias in aliases:
            pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
            if re.search(pattern, resume_lower):
                matched = True
                break
                
        if matched:
            claimed_skills.append(main_skill.capitalize())
            
    return claimed_skills
