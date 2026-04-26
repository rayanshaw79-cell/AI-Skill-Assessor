import streamlit as st
import requests
import uuid
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AI Skill Assessor", layout="wide")

st.title("Conversational AI Skill Assessment 🤖")
st.write("An MVP system to assess job readiness using rule-based heuristics.")

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "is_initialized" not in st.session_state:
    st.session_state.is_initialized = False
if "is_complete" not in st.session_state:
    st.session_state.is_complete = False

# Sidebar for input
with st.sidebar:
    st.header("Candidate Information")
    jd_input = st.text_area("Job Description", height=200, placeholder="Paste Job Description here...")
    resume_input = st.text_area("Candidate Resume", height=200, placeholder="Paste Resume here...")
    
    if st.button("Start Assessment"):
        if jd_input and resume_input:
            with st.spinner("Initializing Assessment..."):
                try:
                    res = requests.post(f"{API_URL}/initialize", json={
                        "session_id": st.session_state.session_id,
                        "jd_text": jd_input,
                        "resume_text": resume_input
                    })
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.is_initialized = True
                        st.session_state.is_complete = False
                        st.session_state.chat_history = []
                        
                        # Add first question
                        msg = f"**Assessing {data['current_skill']}**: {data['next_question']}"
                        st.session_state.chat_history.append({"role": "assistant", "content": msg})
                        st.rerun()
                    else:
                        st.error("Failed to initialize. Please check JD text.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to backend: {e}")
        else:
            st.warning("Please provide both JD and Resume.")

# Chat Interface
if st.session_state.is_initialized and not st.session_state.is_complete:
    st.subheader("Skill Assessment Interview")
    
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Your response..."):
        # Display user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.spinner("Evaluating..."):
            try:
                res = requests.post(f"{API_URL}/chat", json={
                    "session_id": st.session_state.session_id,
                    "response_text": prompt
                })
                
                if res.status_code == 200:
                    data = res.json()
                    if data.get("is_complete"):
                        st.session_state.is_complete = True
                        st.success("Assessment Complete! Generating report...")
                        st.rerun()
                    else:
                        msg = f"**Assessing {data['current_skill']}**: {data['next_question']}"
                        st.session_state.chat_history.append({"role": "assistant", "content": msg})
                        with st.chat_message("assistant"):
                            st.markdown(msg)
                else:
                    st.error("Error communicating with backend.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend: {e}")

# Final Report
if st.session_state.is_complete:
    st.header("📊 Final Assessment Report")
    
    with st.spinner("Fetching Report..."):
        try:
            res = requests.get(f"{API_URL}/report/{st.session_state.session_id}")
            
            if res.status_code == 200:
                report = res.json()
                
                st.subheader(f"Job Readiness Score: {report['job_readiness_score']}%")
                st.progress(min(1.0, report['job_readiness_score'] / 100))
                
                st.write("---")
                st.subheader("Skill Gap Analysis")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Strengths 💪**")
                    if not report['gap_analysis']['strengths']: st.write("None")
                    for s in report['gap_analysis']['strengths']: st.success(s)
                with col2:
                    st.markdown("**Moderate Gaps ⚠️**")
                    if not report['gap_analysis']['moderate']: st.write("None")
                    for s in report['gap_analysis']['moderate']: st.warning(s)
                with col3:
                    st.markdown("**Critical Gaps 🚨**")
                    if not report['gap_analysis']['critical']: st.write("None")
                    for s in report['gap_analysis']['critical']: st.error(s)
                    
                st.divider()
                st.subheader("📚 Personalized Learning Plan")
                
                if not report['learning_plan']:
                    st.write("Excellent! You are highly aligned with the JD. No critical learning plan needed.")
                    
                for item in report['learning_plan']:
                    with st.expander(f"Improve {item['skill']} (Estimated: {item['time_estimate_weeks']} weeks)", expanded=True):
                        st.markdown(f"**Why it matters:** {item['why_it_matters']}")
                        st.markdown(f"**Actionable Steps:** {item['actionable_steps']}")
                        st.markdown(f"**Suggested Resources:** {item['suggested_resources']}")
                        if item.get("adjacent_skills"):
                            st.markdown(f"**Adjacent Skills to Leverage:** {', '.join(item['adjacent_skills'])}")
            else:
                st.error("Failed to fetch report.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to backend: {e}")
