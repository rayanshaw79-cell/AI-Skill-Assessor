import re
from utils.nlp_engine import nlp_engine
from .jd_parser import SKILLS_CONFIG

def evaluate_response(skill: str, question: str, response: str) -> dict:
    """
    Evaluates a user response using semantic NLP and heuristics.
    Returns a dictionary with scores for:
    - accuracy (0.0 to 1.0)
    - depth (0.0 to 1.0)
    - clarity (0.0 to 1.0)
    - applied (0.0 to 1.0)
    """
    response_lower = response.lower()
    words = response_lower.split()
    word_count = len(words)
    
    if word_count == 0:
        return {"accuracy": 0.0, "depth": 0.0, "clarity": 0.0, "applied": 0.0}
    
    # 1. Semantic Accuracy heuristic
    skill_key = skill.lower()
    skill_data = SKILLS_CONFIG.get(skill_key, {})
    conceptual_keywords = skill_data.get("conceptual_keywords", "")
    
    # Target string for semantic comparison
    target_context = f"{skill} {conceptual_keywords}"
    semantic_score = nlp_engine.get_similarity(response_lower, target_context)
    
    # Adjust semantic score to be more generous
    accuracy = min(1.0, max(0.0, (semantic_score - 0.2) / 0.4))
    
    # 2. Depth heuristic
    if word_count > 45:
        depth = 1.0
    elif word_count > 25:
        depth = 0.8
    elif word_count > 15:
        depth = 0.5
    elif word_count > 5:
        depth = 0.2
    else:
        depth = 0.0
        
    # 3. Clarity heuristic
    if 10 < word_count < 120:
        clarity = 1.0
    elif word_count <= 5:
        clarity = 0.3
    else:
        clarity = 0.7
        
    # 4. Semantic Applied heuristic
    applied_references = [
        "I implemented this in a project",
        "I used this to solve a problem",
        "In my previous role, I built",
        "I have hands-on experience with",
        "I designed the architecture for",
        "I managed the deployment of"
    ]
    
    applied_similarities = [nlp_engine.get_similarity(response_lower, ref) for ref in applied_references]
    max_applied_sim = max(applied_similarities) if applied_similarities else 0
    
    applied = min(1.0, max(0.0, (max_applied_sim - 0.3) / 0.4))
    
    return {
        "accuracy": round(accuracy, 2),
        "depth": round(depth, 2),
        "clarity": round(clarity, 2),
        "applied": round(applied, 2)
    }

