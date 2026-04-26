import re

def evaluate_response(skill: str, question: str, response: str) -> dict:
    """
    Evaluates a user response using heuristics.
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
    
    # 1. Accuracy heuristic
    # Check if they mention the skill or related technical terms.
    tech_terms = [
        skill.lower(), 'function', 'class', 'database', 'api', 'model', 
        'server', 'client', 'data', 'architecture', 'system', 'variable', 
        'component', 'library', 'framework', 'code', 'deploy', 'test', 'scale', 'query'
    ]
    matched_terms = sum(1 for term in tech_terms if term in response_lower)
    accuracy = min(1.0, matched_terms / 3.0) # Needs 3 tech terms for full score
    
    # 2. Depth heuristic
    # Based on response length. A longer explanation typically indicates depth in a text chat.
    if word_count > 40:
        depth = 1.0
    elif word_count > 20:
        depth = 0.8
    elif word_count > 10:
        depth = 0.5
    elif word_count > 3:
        depth = 0.2
    else:
        depth = 0.0
        
    # 3. Clarity heuristic
    # Baseline clarity score based on sentence length.
    if 5 < word_count < 100:
        clarity = 0.9
    elif word_count <= 5:
        clarity = 0.4 # Too short
    else:
        clarity = 0.7 # A bit too verbose/run-on
        
    # 4. Applied heuristic
    # Check for words indicating real-world application.
    applied_keywords = [
        "used", "built", "designed", "implemented", "created", 
        "project", "example", "experience", "developed", "team", "production", "work"
    ]
    matched_applied = sum(1 for term in applied_keywords if term in response_lower)
    applied = min(1.0, matched_applied / 2.0) # Needs 2 applied words to get full score
    
    return {
        "accuracy": round(accuracy, 2),
        "depth": round(depth, 2),
        "clarity": round(clarity, 2),
        "applied": round(applied, 2)
    }
