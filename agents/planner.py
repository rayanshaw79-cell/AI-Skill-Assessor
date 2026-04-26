def generate_learning_plan(required_skills: list[dict], skill_scores: dict[str, float]) -> dict:
    """
    Generates a gap analysis and personalized learning plan.
    
    required_skills: list of dicts with 'skill', 'level_required', 'importance'
    skill_scores: dict mapping 'skill' to score (0.0 to 1.0)
    """
    gaps = {"critical": [], "moderate": [], "strengths": []}
    learning_plan = []
    
    # Map for realistic adjacent skill transitions
    adjacent_mapping = {
        "python": ["fastapi", "django", "data analysis", "machine learning"],
        "javascript": ["react", "node.js", "typescript", "vue"],
        "sql": ["data analysis", "postgresql", "mysql"],
        "data analysis": ["machine learning", "pandas", "sql"],
        "machine learning": ["deep learning", "nlp", "llm", "tensorflow", "pytorch"],
        "aws": ["kubernetes", "docker", "ci/cd", "terraform"],
        "lead generation": ["crm", "negotiation", "pipeline management", "sales strategy"],
        "crm": ["lead generation", "account management", "data-driven", "sales strategy"],
        "seo": ["sem", "content marketing", "google analytics", "digital marketing"],
        "content marketing": ["seo", "social media marketing", "brand strategy", "digital marketing"],
        "communication": ["leadership", "collaboration", "negotiation", "strategic thinking"],
        "leadership": ["strategic thinking", "project management", "communication", "collaboration"],
        "strategic thinking": ["leadership", "data-driven", "project management", "market research"]
    }
    
    for req in required_skills:
        skill = req['skill']
        importance = req.get('importance', 0.5)
        
        # Determine target score based on required level
        level_req = req.get('level_required', 'Beginner')
        if level_req == "Advanced":
            target_score = 0.85
        elif level_req == "Intermediate":
            target_score = 0.60
        else:
            target_score = 0.30
            
        actual_score = skill_scores.get(skill, 0.0)
        score_diff = target_score - actual_score
        
        if score_diff <= 0:
            gaps["strengths"].append(skill)
        elif score_diff > 0.4 or (score_diff > 0.2 and importance > 0.7):
            gaps["critical"].append(skill)
        else:
            gaps["moderate"].append(skill)
            
        # If there's a gap, create a learning plan item
        if score_diff > 0:
            # Estimate time based on gap size
            weeks = max(1, int(score_diff * 10))
            
            # Find adjacent skills
            skill_lower = skill.lower()
            adjacent = []
            for k, v in adjacent_mapping.items():
                if skill_lower == k:
                    adjacent = v
                elif skill_lower in v:
                    adjacent.append(k)
                    
            plan_item = {
                "skill": skill,
                "why_it_matters": f"Required at a '{level_req}' level. Criticality: {'High' if importance > 0.7 else 'Medium'}",
                "actionable_steps": f"Focus on building applied projects. You need to bridge the gap from your current score ({int(actual_score*100)}%) to the target ({int(target_score*100)}%).",
                "time_estimate_weeks": weeks,
                "suggested_resources": f"Official documentation, interactive coding platforms, and project-based tutorials on {skill}.",
                "adjacent_skills": list(set(adjacent))[:3] # Max 3 adjacent
            }
            learning_plan.append(plan_item)
            
    return {
        "gap_analysis": gaps,
        "learning_plan": learning_plan
    }
