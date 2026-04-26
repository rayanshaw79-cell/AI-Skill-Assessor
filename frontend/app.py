import streamlit as st
import plotly.graph_objects as go
import requests
import uuid
import os
import math

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AI Skill Assessor", layout="wide", page_icon="🤖")

# ---------------------------------------------------------------------------
# Custom CSS for a polished look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .difficulty-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-left: 8px;
    }
    .badge-beginner     { background: #d1fae5; color: #065f46; }
    .badge-intermediate { background: #fef3c7; color: #92400e; }
    .badge-advanced     { background: #fee2e2; color: #991b1b; }
    .role-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        background: #e0e7ff;
        color: #3730a3;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        text-align: center;
    }
    .metric-card h1 { margin: 0; font-size: 3rem; }
    .metric-card p  { margin: 4px 0 0 0; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

st.title("Conversational AI Skill Assessment 🤖")
st.caption("An adaptive, role-aware system that dynamically adjusts interview difficulty based on your performance.")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "is_initialized" not in st.session_state:
    st.session_state.is_initialized = False
if "is_complete" not in st.session_state:
    st.session_state.is_complete = False
if "total_skills" not in st.session_state:
    st.session_state.total_skills = 0
if "current_skill_number" not in st.session_state:
    st.session_state.current_skill_number = 0
if "current_difficulty" not in st.session_state:
    st.session_state.current_difficulty = "Intermediate"
if "detected_role" not in st.session_state:
    st.session_state.detected_role = "General"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📋 Candidate Information")
    jd_input = st.text_area("Job Description", height=200, placeholder="Paste Job Description here...")
    resume_input = st.text_area("Candidate Resume", height=200, placeholder="Paste Resume here...")

    if st.button("🚀 Start Assessment", use_container_width=True):
        if jd_input and resume_input:
            with st.spinner("Analyzing JD & Resume..."):
                try:
                    res = requests.post(f"{API_URL}/initialize", json={
                        "session_id": st.session_state.session_id,
                        "jd_text": jd_input,
                        "resume_text": resume_input,
                    })
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.is_initialized = True
                        st.session_state.is_complete = False
                        st.session_state.chat_history = []
                        st.session_state.total_skills = data.get("total_skills", 1)
                        st.session_state.current_skill_number = data.get("current_skill_number", 1)
                        st.session_state.current_difficulty = data.get("difficulty_level", "Intermediate")
                        st.session_state.detected_role = data.get("detected_role", "General")

                        # Show fallback warning if the JD was non-technical
                        if data.get("fallback_used"):
                            st.warning(data["message"])

                        msg = f"**Assessing {data['current_skill']}**: {data['next_question']}"
                        st.session_state.chat_history.append({"role": "assistant", "content": msg})
                        st.rerun()
                    else:
                        st.error("Failed to initialize. Please check your JD text.")
                except requests.exceptions.RequestException as e:
                    st.error(f"⚠️ Could not reach the backend at `{API_URL}`. Is the API server running?\n\n`{e}`")
        else:
            st.warning("Please provide both a JD and a Resume.")

    # Show interview metadata in the sidebar while active
    if st.session_state.is_initialized and not st.session_state.is_complete:
        st.divider()
        st.markdown(f"**Detected Role:** <span class='role-tag'>{st.session_state.detected_role}</span>", unsafe_allow_html=True)

        diff = st.session_state.current_difficulty
        badge_class = f"badge-{diff.lower()}"
        st.markdown(f"**Current Difficulty:** <span class='difficulty-badge {badge_class}'>{diff}</span>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Progress bar (only during active interview)
# ---------------------------------------------------------------------------
if st.session_state.is_initialized and not st.session_state.is_complete:
    total = st.session_state.total_skills
    current = st.session_state.current_skill_number
    progress = current / total if total > 0 else 0
    st.progress(progress, text=f"📝 Assessing skill {current} of {total}")


# ---------------------------------------------------------------------------
# Chat Interface
# ---------------------------------------------------------------------------
if st.session_state.is_initialized and not st.session_state.is_complete:
    st.subheader("💬 Skill Assessment Interview")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your answer here..."):
        # Display user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Evaluating your response..."):
            try:
                res = requests.post(f"{API_URL}/chat", json={
                    "session_id": st.session_state.session_id,
                    "response_text": prompt,
                })

                if res.status_code == 200:
                    data = res.json()
                    if data.get("is_complete"):
                        st.session_state.is_complete = True
                        st.success("✅ Assessment Complete! Generating your report...")
                        st.rerun()
                    else:
                        # Update progress & difficulty state
                        st.session_state.current_skill_number = data.get("current_skill_number", st.session_state.current_skill_number)
                        st.session_state.total_skills = data.get("total_skills", st.session_state.total_skills)
                        st.session_state.current_difficulty = data.get("difficulty_level", "Intermediate")

                        # Build the agentic transition + next question message
                        transition = data.get("transition_message", "")
                        question_text = f"**Assessing {data['current_skill']}**: {data['next_question']}"
                        full_msg = f"_{transition}_\n\n{question_text}" if transition else question_text

                        st.session_state.chat_history.append({"role": "assistant", "content": full_msg})
                        with st.chat_message("assistant"):
                            st.markdown(full_msg)
                else:
                    st.error("Error communicating with backend.")
            except requests.exceptions.RequestException as e:
                st.error(f"⚠️ Connection error: {e}")

# ---------------------------------------------------------------------------
# Final Report with Radar Chart
# ---------------------------------------------------------------------------
if st.session_state.is_complete:
    st.header("📊 Final Assessment Report")

    with st.spinner("Fetching your report..."):
        try:
            res = requests.get(f"{API_URL}/report/{st.session_state.session_id}")

            if res.status_code == 200:
                report = res.json()

                # ---- Hero metric row ----
                col_score, col_role = st.columns([1, 1])
                with col_score:
                    readiness = report["job_readiness_score"]
                    st.markdown(f"""
                    <div class="metric-card">
                        <h1>{readiness}%</h1>
                        <p>Job Readiness Score</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_role:
                    st.markdown(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                        <h1>{report['detected_role']}</h1>
                        <p>Detected Role Profile</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")  # spacer

                # ---- Radar Chart: Required vs Demonstrated ----
                st.subheader("🎯 Skill Radar — Required vs Demonstrated")

                skill_scores = report["skill_scores"]
                required_levels = report.get("required_levels", {})
                skills = list(skill_scores.keys())

                if skills:
                    # Plotly figure initialization

                    demonstrated = [round(skill_scores[s], 2) for s in skills]
                    required = [round(required_levels.get(s, 0.5), 2) for s in skills]

                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=required + [required[0]],
                        theta=skills + [skills[0]],
                        fill="toself",
                        name="Required Level",
                        line=dict(color="#f5576c"),
                        opacity=0.6,
                    ))
                    fig.add_trace(go.Scatterpolar(
                        r=demonstrated + [demonstrated[0]],
                        theta=skills + [skills[0]],
                        fill="toself",
                        name="Your Score",
                        line=dict(color="#667eea"),
                        opacity=0.7,
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                        showlegend=True,
                        template="plotly_dark",
                        height=450,
                        margin=dict(t=40, b=40),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # ---- Per-skill score table ----
                    st.subheader("📈 Score Breakdown")
                    score_data = []
                    for s in skills:
                        actual = skill_scores[s]
                        req = required_levels.get(s, 0.5)
                        gap = req - actual
                        status = "✅ Strong" if gap <= 0 else ("⚠️ Moderate Gap" if gap < 0.3 else "🚨 Critical Gap")
                        score_data.append({
                            "Skill": s,
                            "Your Score": f"{int(actual * 100)}%",
                            "Required": f"{int(req * 100)}%",
                            "Status": status,
                        })
                    st.table(score_data)

                # ---- Gap Analysis ----
                st.divider()
                st.subheader("🔍 Skill Gap Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Strengths 💪**")
                    if not report["gap_analysis"]["strengths"]:
                        st.write("None identified")
                    for s in report["gap_analysis"]["strengths"]:
                        st.success(s)
                with col2:
                    st.markdown("**Moderate Gaps ⚠️**")
                    if not report["gap_analysis"]["moderate"]:
                        st.write("None")
                    for s in report["gap_analysis"]["moderate"]:
                        st.warning(s)
                with col3:
                    st.markdown("**Critical Gaps 🚨**")
                    if not report["gap_analysis"]["critical"]:
                        st.write("None")
                    for s in report["gap_analysis"]["critical"]:
                        st.error(s)

                # ---- Learning Plan ----
                st.divider()
                st.subheader("📚 Personalized Learning Plan")

                if not report["learning_plan"]:
                    st.balloons()
                    st.write("🎉 Excellent! You are highly aligned with the JD. No critical learning plan needed.")

                for item in report["learning_plan"]:
                    with st.expander(f"📘 Improve **{item['skill']}** (Est. {item['time_estimate_weeks']} weeks)", expanded=True):
                        st.markdown(f"**Why it matters:** {item['why_it_matters']}")
                        st.markdown(f"**Actionable Steps:** {item['actionable_steps']}")
                        st.markdown(f"**Suggested Resources:** {item['suggested_resources']}")
                        if item.get("adjacent_skills"):
                            st.markdown(f"**Adjacent Skills to Leverage:** {', '.join(item['adjacent_skills'])}")
            else:
                st.error("Failed to fetch report.")
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Connection error: {e}")
