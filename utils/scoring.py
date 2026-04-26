def calculate_response_score(accuracy: float, depth: float, clarity: float, applied: float) -> float:
    """
    Calculates the score of a single conversational response based on heuristics.
    Weights:
    - Accuracy: 30%
    - Depth: 30%
    - Clarity: 20%
    - Applied: 20%
    
    All inputs should be floats between 0.0 and 1.0.
    Returns a final score between 0.0 and 1.0.
    """
    score = (0.3 * accuracy) + (0.3 * depth) + (0.2 * clarity) + (0.2 * applied)
    # Ensure it's capped at 1.0
    return min(1.0, max(0.0, score))

def calculate_job_readiness(skill_scores: dict[str, float]) -> float:
    """
    Calculates the overall job readiness score as a percentage.
    Takes a dictionary mapping skill names to their scores (0.0 to 1.0).
    """
    if not skill_scores:
        return 0.0
        
    scores = list(skill_scores.values())
    average_score = sum(scores) / len(scores)
    
    return round(average_score * 100, 2)
