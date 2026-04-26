import re
import json
import os

# Load skills configuration
skills_file_path = os.path.join(os.path.dirname(__file__), '..', 'skills.json')
with open(skills_file_path, 'r') as f:
    SKILLS_CONFIG = json.load(f)

# Keep COMMON_SKILLS for backward compatibility
COMMON_SKILLS = list(SKILLS_CONFIG.keys())

# Role clusters: maps a role name to the set of skills that signal it
ROLE_CLUSTERS = {
    "Data Science": {"machine learning", "deep learning", "nlp", "computer vision",
                     "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn",
                     "data analysis", "llm"},
    "Backend":      {"python", "java", "golang", "fastapi", "django", "flask",
                     "spring", "sql", "mysql", "postgresql", "mongodb", "redis",
                     "elasticsearch", "node.js"},
    "DevOps":       {"aws", "gcp", "azure", "docker", "kubernetes", "terraform",
                     "ci/cd"},
    "Frontend":     {"react", "angular", "vue", "typescript", "javascript"},
}


def parse_jd(jd_text: str) -> list[dict]:
    """
    Parses a Job Description text and extracts required skills.
    Returns a list of dictionaries with keys:
    - skill
    - level_required (Beginner, Intermediate, Advanced)
    - importance (0.0 to 1.0)
    """
    jd_lower = jd_text.lower()
    extracted_skills = []
    
    # Simple heuristics to detect level requirements
    advanced_keywords = ["expert", "senior", "advanced", "architect", "lead", "deep understanding", "proficient"]
    intermediate_keywords = ["intermediate", "mid-level", "experience with", "working knowledge", "familiarity"]
    
    for main_skill, aliases in SKILLS_CONFIG.items():
        # Check if any alias exists in JD
        matched = False
        count = 0
        for alias in aliases:
            # Handle special characters in regex using lookarounds instead of \b 
            # since \b treats '.' and '+' as non-word chars.
            pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
            matches = re.findall(pattern, jd_lower)
            if matches:
                matched = True
                count += len(matches)
                
        if matched:
            # Default level
            level = "Beginner"
            importance = 0.5
            
            # Determine level based on context window around the skill
            # (Very rudimentary heuristic: check entire text or just nearby)
            is_advanced = any(kw in jd_lower for kw in advanced_keywords)
            is_intermediate = any(kw in jd_lower for kw in intermediate_keywords)
            
            if is_advanced:
                level = "Advanced"
                importance = 1.0
            elif is_intermediate:
                level = "Intermediate"
                importance = 0.8
                
            # If the skill appears multiple times, it might be more important
            if count > 2:
                importance = min(1.0, importance + 0.2)
                
            extracted_skills.append({
                "skill": main_skill.capitalize(),
                "level_required": level,
                "importance": round(importance, 2)
            })
            
    return extracted_skills


def detect_role(required_skills: list[dict]) -> str:
    """
    Infers the primary role from a list of extracted skills by counting
    how many skills in each role cluster are present in the JD.

    Returns the best-matching role name, or "General" if no clear cluster is found.
    """
    skill_names = {s["skill"].lower() for s in required_skills}
    scores = {}

    for role, cluster in ROLE_CLUSTERS.items():
        overlap = skill_names & cluster
        scores[role] = len(overlap)

    if not any(scores.values()):
        return "General"

    best_role = max(scores, key=scores.get)

    # Only assign the role if there are at least 2 matching signals
    if scores[best_role] >= 2:
        return best_role

    return "General"
