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
    "Data Science": {
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn",
        "data analysis", "llm"
    },
    "Backend": {
        "python", "java", "golang", "fastapi", "django", "flask",
        "spring", "sql", "mysql", "postgresql", "mongodb", "redis",
        "elasticsearch", "node.js"
    },
    "DevOps": {
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd"
    },
    "Frontend": {
        "react", "angular", "vue", "typescript", "javascript"
    },
    "Sales": {
        "lead generation", "crm", "negotiation", "pipeline management",
        "account management", "b2b sales", "b2c sales", "cold calling",
        "sales strategy"
    },
    "Marketing": {
        "seo", "sem", "content marketing", "social media marketing",
        "email marketing", "brand strategy", "google analytics",
        "market research", "product marketing", "digital marketing"
    },
    "Management": {
        "leadership", "project management", "strategic thinking",
        "collaboration", "communication", "data-driven"
    },
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
    advanced_keywords = [
        "expert", "senior", "advanced", "architect", "lead",
        "deep understanding", "proficient", "extensive experience"
    ]
    intermediate_keywords = [
        "intermediate", "mid-level", "experience with",
        "working knowledge", "familiarity", "2+ years", "3+ years"
    ]

    for main_skill, aliases in SKILLS_CONFIG.items():
        matched = False
        count = 0
        for alias in aliases:
            # Handle special characters in regex using lookarounds
            pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
            matches = re.findall(pattern, jd_lower)
            if matches:
                matched = True
                count += len(matches)

        if matched:
            level = "Beginner"
            importance = 0.5

            is_advanced = any(kw in jd_lower for kw in advanced_keywords)
            is_intermediate = any(kw in jd_lower for kw in intermediate_keywords)

            if is_advanced:
                level = "Advanced"
                importance = 1.0
            elif is_intermediate:
                level = "Intermediate"
                importance = 0.8

            # Skills mentioned multiple times are more important
            if count > 2:
                importance = min(1.0, importance + 0.2)

            extracted_skills.append({
                "skill": main_skill,
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

    # Only assign the role if there is at least 1 matching signal
    # (lowered from 2 to handle smaller non-tech JDs that may only list 1-2 skills)
    if scores[best_role] >= 1:
        return best_role

    return "General"
