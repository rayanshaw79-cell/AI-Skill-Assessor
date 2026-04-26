import json
import os
import random

# Load the rich question bank from JSON
_questions_path = os.path.join(os.path.dirname(__file__), '..', 'questions.json')
with open(_questions_path, 'r') as f:
    QUESTION_BANK = json.load(f)

# Adaptive difficulty: if a candidate scores above this, escalate level; below → de-escalate
ESCALATE_THRESHOLD = 0.8
DEESCALATE_THRESHOLD = 0.35

# Level ordering for adaptive escalation/de-escalation
LEVELS = ["Beginner", "Intermediate", "Advanced"]


def _resolve_level(level: str, last_score: float | None) -> str:
    """
    Adjusts the difficulty level based on the candidate's last score.
    - Score > 0.8: escalate to next level (e.g., Intermediate → Advanced)
    - Score < 0.35: de-escalate to previous level (e.g., Advanced → Intermediate)
    - Otherwise: keep same level
    """
    if last_score is None:
        return level

    current_idx = LEVELS.index(level) if level in LEVELS else 1  # Default to Intermediate index

    if last_score >= ESCALATE_THRESHOLD and current_idx < len(LEVELS) - 1:
        return LEVELS[current_idx + 1]
    elif last_score <= DEESCALATE_THRESHOLD and current_idx > 0:
        return LEVELS[current_idx - 1]

    return level


def _find_skill_key(skill: str) -> str | None:
    """
    Fuzzy-matches a skill name against QUESTION_BANK keys.
    e.g. 'Machine Learning' -> 'machine learning'
    """
    skill_lower = skill.lower().strip()
    for key in QUESTION_BANK:
        if key in skill_lower or skill_lower in key:
            return key
    return None


def get_dynamic_question(
    skill: str,
    level: str = "Intermediate",
    role: str = "General",
    last_score: float | None = None,
    exclude: list[str] | None = None
) -> tuple[str, str]:
    """
    Waterfall Question Selector.

    Priority:
    1. Role-specific pool for the resolved level.
    2. Role-specific pool for adjacent levels (breadth fallback).
    3. General pool for the resolved level.
    4. General pool for any level.
    5. Template-based generic question.

    Args:
        skill: The skill being assessed (e.g., "Python").
        level: Base difficulty ("Beginner", "Intermediate", "Advanced").
        role: Candidate's detected role (e.g., "Backend", "Data Science", "DevOps").
        last_score: Score from the previous skill question (0.0-1.0). Used for adaptive difficulty.
        exclude: List of question strings already asked this session.

    Returns:
        A tuple of (question_text, actual_level_used).
    """
    exclude = exclude or []
    resolved_level = _resolve_level(level, last_score)
    skill_key = _find_skill_key(skill)

    if skill_key:
        skill_data = QUESTION_BANK[skill_key]

        # --- WATERFALL ---

        # Step 1: Role-specific, exact resolved level
        questions = skill_data.get(role, {}).get(resolved_level, [])
        available = [q for q in questions if q not in exclude]
        if available:
            return random.choice(available), resolved_level

        # Step 2: Role-specific, any level (breadth fallback within the role)
        for lvl in LEVELS:
            if lvl == resolved_level:
                continue
            questions = skill_data.get(role, {}).get(lvl, [])
            available = [q for q in questions if q not in exclude]
            if available:
                return random.choice(available), lvl

        # Step 3: General pool, exact resolved level
        questions = skill_data.get("General", {}).get(resolved_level, [])
        available = [q for q in questions if q not in exclude]
        if available:
            return random.choice(available), resolved_level

        # Step 4: General pool, any level
        for lvl in LEVELS:
            questions = skill_data.get("General", {}).get(lvl, [])
            available = [q for q in questions if q not in exclude]
            if available:
                return random.choice(available), lvl

    # Step 5: Template-based generic question (never fails)
    templates = {
        "Beginner":     f"Can you describe your basic understanding of {skill}?",
        "Intermediate": f"Could you share an example of a project where you actively used {skill}?",
        "Advanced":     f"Can you explain a complex architectural or design challenge you solved using {skill}?",
    }
    return templates.get(resolved_level, f"Can you elaborate on your experience with {skill}?"), resolved_level


# --- Backward-compatible wrapper so existing callers don't break ---
def get_question(skill: str, level: str = "Intermediate") -> str:
    question, _ = get_dynamic_question(skill=skill, level=level)
    return question

