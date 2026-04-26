---
title: AI Skill Assessor
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# AI Skill Assessor 🤖

An intelligent, role-aware, and adaptive skill assessment system designed to evaluate candidate readiness through conversational technical interviews.

## 🚀 Overview
The **AI Skill Assessor** transforms static evaluations into dynamic, context-aware technical interviews. It parses Job Descriptions (JDs) and Resumes, detects the primary engineering role, and conducts a structured interview using a "Waterfall" selection engine and adaptive difficulty scaling.

## ✨ Key Features
- **Intelligent Role Detection**: Automatically categorizes candidates into **Backend**, **Frontend**, **Data Science**, or **DevOps** based on skill clusters extracted from the JD.
- **Waterfall Question Selection**: A hierarchical engine that prioritizes role-specific questions, falling back to general pools only when necessary.
- **Adaptive Difficulty (Escalator Logic)**: Dynamically adjusts the interview difficulty (Beginner → Intermediate → Advanced) based on the candidate's real-time performance.
- **Alias-Aware Skill Parsing**: Robust regex-based skill extraction that understands variations (e.g., "K8s" vs "Kubernetes", "Node" vs "Node.js").
- **Session Persistence**: SQLite-backed session management allows for interview continuity and stateful tracking.
- **No-Cost Heuristics**: Operates entirely locally with high-performance rule-based evaluation—no expensive LLM API calls required.

## 🛠️ Project Architecture
```text
AI Skill Assessor/
├── agents/                 # Intelligent logic units
│   ├── jd_parser.py        # JD analysis & Role detection
│   ├── resume_analyzer.py  # Resume skill extraction
│   ├── conversational_assessor.py # Response evaluation engine
│   └── planner.py          # Gap analysis & Learning plan generator
├── api/                    # FastAPI Backend
│   └── main.py             # Session & Endpoint management
├── frontend/               # Streamlit UI
│   └── app.py              # Chat interface & Report visualization
├── utils/                  # Shared utilities
│   ├── database.py         # SQLite persistence layer
│   ├── question_bank.py    # Waterfall selection engine
│   └── scoring.py          # Heuristic scoring logic
├── data/                   # Configuration files
│   ├── skills.json         # Skill aliases & taxonomy
│   └── questions.json      # Role-stratified question bank
└── requirements.txt        # System dependencies
```

## 🏁 Getting Started

### 1. Prerequisites
- Python 3.9 or higher
- `pip` (Python package manager)

### 2. Installation
Clone the repository and install the required packages:
```bash
git clone <your-repo-url>
cd AI-Skill-Assessor
pip install -r requirements.txt
```

### 3. Running the Application
The system requires both the Backend and Frontend to be running.

**Step A: Start the Backend (FastAPI)**
```bash
python -m uvicorn api.main:app --reload
```
*Running at: `http://127.0.0.1:8000`*

**Step B: Start the Frontend (Streamlit)**
```bash
python -m streamlit run frontend/app.py
```
*Running at: `http://localhost:8501`*

---

## 🚢 Deployment

### Deploying to Hugging Face Spaces (Free)
This project is configured to run on Hugging Face Spaces using Docker.

1.  **Create a New Space**: Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2.  **Select SDK**: Choose **Docker**.
3.  **Choose Template**: Select **Blank** (or any simple Docker template).
4.  **Upload Files**: You can either connect your GitHub repository or upload the files directly.
5.  **Wait for Build**: Hugging Face will automatically detect the `Dockerfile`, run the `start.sh` script, and expose the application on port 7860.

---

## 📝 Sample Input & Output

### Sample Input
**Job Description:**
> "Looking for a Senior Backend Engineer proficient in Python, FastAPI, and SQL. Experience with AWS and Docker is a plus."

**Candidate Resume:**
> "Experienced developer with a background in Python and PostgreSQL. Built several web APIs and managed basic cloud deployments."

### Sample Output (Assessment Flow)
1. **Role Detected**: `Backend`
2. **First Question (Python - Intermediate)**: *"How does Python's garbage collection work? What is reference counting?"*
3. **Candidate Response**: *"Python uses reference counting to track objects. When the count drops to zero, the object is deallocated..."*
4. **Adaptive Shift**: Since the candidate provided a strong answer (Score > 0.8), the next question for SQL might escalate to **Advanced**.
5. **Final Report**:
   - **Job Readiness Score**: `84%`
   - **Gaps Identified**: AWS (Deployment strategies), Docker (Multi-stage builds).
   - **Learning Plan**: 4-week roadmap to bridge the cloud/DevOps gap.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
