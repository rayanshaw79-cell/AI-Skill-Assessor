import random

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.jd_parser import parse_jd, detect_role
from agents.resume_analyzer import analyze_resume
from agents.conversational_assessor import evaluate_response
from agents.planner import generate_learning_plan
from utils.scoring import calculate_response_score, calculate_job_readiness
from utils.question_bank import get_dynamic_question
from utils.database import get_session, save_session

app = FastAPI(title="AI Skill Assessor API")

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all. Refine for production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class InitRequest(BaseModel):
    session_id: str
    jd_text: str
    resume_text: str


class ChatRequest(BaseModel):
    session_id: str
    response_text: str


# ---------------------------------------------------------------------------
# Agentic transition generator
# ---------------------------------------------------------------------------
_POSITIVE_TRANSITIONS = [
    "Excellent breakdown — you clearly have strong hands-on experience with {prev}.",
    "That was a thorough answer on {prev}. Your depth of understanding really shows.",
    "Great insight on {prev}! I can see you've worked with this in real projects.",
    "Solid response on {prev}. You demonstrated both theory and practical knowledge.",
]

_NEUTRAL_TRANSITIONS = [
    "Thanks for sharing your thoughts on {prev}.",
    "Got it — let's keep the momentum going.",
    "Noted. Let's move on to the next area.",
]

_ENCOURAGING_TRANSITIONS = [
    "Thanks for your answer on {prev}. Don't worry — there are many areas to shine in.",
    "Appreciate the effort on {prev}. Let's explore another skill area now.",
    "That's a good start on {prev}. Let's see how you do with the next topic.",
]


def _generate_transition(prev_skill: str, score: float) -> str:
    """Generate a context-aware conversational transition between questions."""
    if score >= 0.8:
        template = random.choice(_POSITIVE_TRANSITIONS)
    elif score >= 0.5:
        template = random.choice(_NEUTRAL_TRANSITIONS)
    else:
        template = random.choice(_ENCOURAGING_TRANSITIONS)
    return template.format(prev=prev_skill)


# ---------------------------------------------------------------------------
# Graceful fallback skills for non-technical JDs
# ---------------------------------------------------------------------------
_FALLBACK_SKILLS = [
    {"skill": "Python", "level_required": "Intermediate", "importance": 0.7},
    {"skill": "SQL", "level_required": "Beginner", "importance": 0.6},
    {"skill": "Machine Learning", "level_required": "Beginner", "importance": 0.5},
]


# ---------------------------------------------------------------------------
# POST /initialize
# ---------------------------------------------------------------------------
@app.post("/initialize")
def initialize(req: InitRequest):
    required_skills = parse_jd(req.jd_text)
    claimed_skills = analyze_resume(req.resume_text)

    # Graceful fallback: if JD yields zero detectable skills, use a
    # general Software Engineering baseline and flag the user.
    fallback_used = False
    if not required_skills:
        required_skills = _FALLBACK_SKILLS
        fallback_used = True

    # Detect the primary role to drive role-aware question selection
    role = detect_role(required_skills)

    first_skill = required_skills[0]
    question, level_used = get_dynamic_question(
        skill=first_skill["skill"],
        level=first_skill["level_required"],
        role=role,
    )

    session_data = {
        "required_skills": required_skills,
        "claimed_skills": claimed_skills,
        "role": role,
        "current_skill_index": 0,
        "total_skills": len(required_skills),
        "skill_scores": {},
        "last_score": None,
        "asked_questions": [question],
        "is_complete": False,
    }
    save_session(req.session_id, session_data)

    init_message = (
        "No specific technical skills were detected in the JD. "
        "Proceeding with a General Software Engineering assessment."
        if fallback_used
        else "Initialization successful."
    )

    return {
        "message": init_message,
        "fallback_used": fallback_used,
        "detected_role": role,
        "skills_to_assess": [s["skill"] for s in required_skills],
        "total_skills": len(required_skills),
        "claimed_skills": claimed_skills,
        "next_question": question,
        "current_skill": first_skill["skill"],
        "current_skill_number": 1,
        "difficulty_level": level_used,
    }


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session["is_complete"]:
        return {"is_complete": True, "message": "Assessment is already complete."}

    current_index = session["current_skill_index"]
    required_skills = session["required_skills"]
    current_skill = required_skills[current_index]

    # Evaluate response
    eval_result = evaluate_response(current_skill["skill"], "", req.response_text)

    # Calculate score
    final_score = calculate_response_score(
        eval_result["accuracy"],
        eval_result["depth"],
        eval_result["clarity"],
        eval_result["applied"],
    )

    # Store score and update adaptive state
    session["skill_scores"][current_skill["skill"]] = final_score
    session["last_score"] = final_score

    # Move to next skill
    session["current_skill_index"] += 1
    total = session.get("total_skills", len(required_skills))

    if session["current_skill_index"] >= len(required_skills):
        session["is_complete"] = True
        save_session(req.session_id, session)
        return {
            "is_complete": True,
            "message": "Assessment complete! Generating report...",
            "last_score": round(final_score, 2),
        }

    next_skill = required_skills[session["current_skill_index"]]

    # Dynamic selection: role-aware + adaptive difficulty + no repeats
    question, level_used = get_dynamic_question(
        skill=next_skill["skill"],
        level=next_skill["level_required"],
        role=session.get("role", "General"),
        last_score=session["last_score"],
        exclude=session.get("asked_questions", []),
    )
    session["asked_questions"].append(question)

    # Agentic conversational transition
    transition = _generate_transition(current_skill["skill"], final_score)

    save_session(req.session_id, session)
    return {
        "is_complete": False,
        "transition_message": transition,
        "next_question": question,
        "current_skill": next_skill["skill"],
        "current_skill_number": session["current_skill_index"] + 1,
        "total_skills": total,
        "difficulty_level": level_used,
        "last_score": round(final_score, 2),
    }


# ---------------------------------------------------------------------------
# GET /report/{session_id}
# ---------------------------------------------------------------------------
@app.get("/report/{session_id}")
def get_report(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if not session["is_complete"]:
        raise HTTPException(status_code=400, detail="Assessment not complete.")

    job_readiness = calculate_job_readiness(session["skill_scores"])
    plan = generate_learning_plan(session["required_skills"], session["skill_scores"])

    # Build required-level mapping for the radar chart
    required_levels = {}
    for s in session["required_skills"]:
        level = s.get("level_required", "Beginner")
        required_levels[s["skill"]] = {"Advanced": 1.0, "Intermediate": 0.6, "Beginner": 0.3}.get(level, 0.5)

    return {
        "job_readiness_score": job_readiness,
        "detected_role": session.get("role", "General"),
        "skill_scores": session["skill_scores"],
        "required_levels": required_levels,
        "gap_analysis": plan["gap_analysis"],
        "learning_plan": plan["learning_plan"],
    }
