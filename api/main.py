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

# Setup CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all. Refine for production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InitRequest(BaseModel):
    session_id: str
    jd_text: str
    resume_text: str

class ChatRequest(BaseModel):
    session_id: str
    response_text: str


@app.post("/initialize")
def initialize(req: InitRequest):
    required_skills = parse_jd(req.jd_text)
    claimed_skills = analyze_resume(req.resume_text)

    if not required_skills:
        # Fallback if JD is too generic for our heuristics
        required_skills = [{"skill": "Python", "level_required": "Intermediate", "importance": 0.8}]

    # Detect the primary role to drive role-aware question selection
    role = detect_role(required_skills)

    first_skill = required_skills[0]
    question, level_used = get_dynamic_question(
        skill=first_skill['skill'],
        level=first_skill['level_required'],
        role=role
    )

    session_data = {
        "required_skills": required_skills,
        "claimed_skills": claimed_skills,
        "role": role,
        "current_skill_index": 0,
        "skill_scores": {},
        "last_score": None,          # tracks last answer score for adaptive difficulty
        "asked_questions": [question],  # prevents repeating the same question
        "is_complete": False
    }
    save_session(req.session_id, session_data)

    return {
        "message": "Initialization successful.",
        "detected_role": role,
        "skills_to_assess": [s['skill'] for s in required_skills],
        "claimed_skills": claimed_skills,
        "next_question": question,
        "current_skill": first_skill['skill'],
        "difficulty_level": level_used,
    }


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
    eval_result = evaluate_response(current_skill['skill'], "", req.response_text)

    # Calculate score
    final_score = calculate_response_score(
        eval_result['accuracy'],
        eval_result['depth'],
        eval_result['clarity'],
        eval_result['applied']
    )

    # Store score and update the last_score for adaptive difficulty on the NEXT skill
    session["skill_scores"][current_skill['skill']] = final_score
    session["last_score"] = final_score

    # Move to next skill
    session["current_skill_index"] += 1
    if session["current_skill_index"] >= len(required_skills):
        session["is_complete"] = True
        save_session(req.session_id, session)
        return {
            "is_complete": True,
            "message": "Assessment complete! Generating report..."
        }

    next_skill = required_skills[session["current_skill_index"]]

    # Dynamic selection: role-aware + adaptive difficulty + no repeats
    question, level_used = get_dynamic_question(
        skill=next_skill['skill'],
        level=next_skill['level_required'],
        role=session.get("role", "General"),
        last_score=session["last_score"],
        exclude=session.get("asked_questions", [])
    )
    session["asked_questions"].append(question)

    save_session(req.session_id, session)
    return {
        "is_complete": False,
        "next_question": question,
        "current_skill": next_skill['skill'],
        "difficulty_level": level_used,
        "last_score": round(final_score, 2),
    }


@app.get("/report/{session_id}")
def get_report(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if not session["is_complete"]:
        raise HTTPException(status_code=400, detail="Assessment not complete.")

    job_readiness = calculate_job_readiness(session["skill_scores"])
    plan = generate_learning_plan(session["required_skills"], session["skill_scores"])

    return {
        "job_readiness_score": job_readiness,
        "detected_role": session.get("role", "General"),
        "skill_scores": session["skill_scores"],
        "gap_analysis": plan["gap_analysis"],
        "learning_plan": plan["learning_plan"]
    }
