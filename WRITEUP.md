# AI Skill Assessor: Approach, Architecture & Trade-offs

## 1. The Approach
The AI Skill Assessor is designed to simulate a dynamic, conversational technical interview without relying on continuous, expensive calls to external Large Language Models (LLMs). The core methodology follows a **Role-Aware, Adaptive Assessment Loop**:

*   **Intelligent Parsing:** The system extracts the Job Description (JD) and the candidate's Resume. It uses a regex-backed taxonomy engine to map aliases (e.g., "K8s" to "Kubernetes") and identify the primary job role (Backend, Sales, Frontend, etc.).
*   **Waterfall Question Engine:** Questions are stratified into Beginner, Intermediate, and Advanced tiers. The system employs an "escalator" logic: a candidate starts at an Intermediate level. A strong answer promotes them to an Advanced question for the next skill, while a poor answer scales the difficulty down to Beginner, ensuring a customized candidate experience.
*   **Heuristic Evaluation:** Instead of using an LLM to grade answers, the system uses a custom heuristic scoring algorithm. It evaluates responses based on keyword context matching (accuracy), word count thresholds (depth), structural markers (clarity), and action-oriented vocabulary like "built", "managed", or "led" (practical application).
*   **Gap Analysis & Planning:** Upon completion, the system generates a quantified "Job Readiness Score," maps demonstrated skills against required levels on a Radar Chart, and outputs an actionable, week-by-week learning plan that includes adjacent skill suggestions.

## 2. System Architecture
The application is built on a modular, decoupled architecture prioritizing speed and local execution.

*   **Frontend (Streamlit):** A pure presentation layer running on Port `8501`. It handles the user interface, session visualization, and renders dynamic Plotly charts. It maintains no business logic, acting strictly as an API consumer.
*   **Backend (FastAPI):** The central orchestration layer running on Port `8000`. It exposes RESTful endpoints (`/initialize`, `/chat`, `/report`) and manages application state.
*   **Modular "Agents":** The business logic is isolated into specific agent modules:
    *   `jd_parser.py`: Maps JD text to predefined role clusters.
    *   `resume_analyzer.py`: Extracts and normalizes candidate skills.
    *   `conversational_assessor.py`: The heuristic scoring engine evaluating real-time chat responses.
    *   `planner.py`: Aggregates scores to generate the final personalized report.
*   **Data Persistence (SQLite):** Chat histories, current skill indices, and interim scores are persisted locally in `sessions.db`. This allows for stateless API calls and ensures interview continuity even if the frontend refreshes.
*   **Containerization (Docker):** The entire stack is bundled via Docker and orchestrated via a `start.sh` script, exposing a unified interface for platforms like Hugging Face Spaces.

## 3. Trade-offs & Engineering Decisions

### **Heuristic Scoring vs. Generative LLMs**
*   **The Decision:** We opted for a sophisticated keyword/heuristic engine for grading answers instead of sending every user message to a model like GPT-4.
*   **Pros:** **$0 Operational Cost**, near-zero latency, absolute deterministic reliability, and complete data privacy (no candidate data is sent to external APIs).
*   **Cons:** The system evaluates the *presence* of knowledge markers rather than deep semantic comprehension. A candidate could theoretically "keyword stuff" an answer without forming a coherent sentence and still score reasonably well.

### **SQLite Local Persistence vs. Cloud Databases (PostgreSQL/Redis)**
*   **The Decision:** We used a local SQLite file (`utils/database.py`) to handle session state rather than spinning up a Redis cache or a managed PostgreSQL instance.
*   **Pros:** Extreme portability. The application can run locally on any machine instantly without complex environment variable configurations or cloud dependencies. 
*   **Cons:** Not suitable for horizontal scaling. If the FastAPI backend were scaled across multiple worker nodes behind a load balancer, they would not share the same SQLite file.

### **Rule-Based Role Clustering vs. Vector Embeddings**
*   **The Decision:** Roles are detected using hardcoded clusters (`ROLE_CLUSTERS` in `jd_parser.py`) mapping specific skills to roles, rather than using semantic vector embeddings.
*   **Pros:** Highly transparent, easy to debug, and requires no ML models to be loaded into memory, keeping the Docker image lightweight.
*   **Cons:** Inflexible with highly ambiguous or "hybrid" job descriptions. If a JD doesn't heavily feature our predefined taxonomy terms, the system aggressively falls back to "General Professional" evaluation, potentially missing nuances.
