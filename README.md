# SkillPath AI
## AI-Powered Competency Gap & Personalized Learning Platform

A Streamlit prototype that assesses a learner's competencies, calculates skill gaps, recommends curated resources, generates personalized learning plans and practice quizzes, and tracks progress.

### Combined team contributions
- **Member 1 — UI, student workflow & integration:** Streamlit pages, profile, navigation, login, workflow integration.
- **Member 2 — Competency framework, assessment & gap analysis:** competency/question datasets, validation, per-skill scoring, gap formula and priority labels.
- **Member 3 — Agentic AI & prompt engineering:** Gemini-based learning-plan and practice-question generation, output validation, fallback behavior.
- **Member 4 — Resource recommendation, analytics & progress:** curated resources, recommendation matching, CSV task/assessment storage and charts.

### Main workflow
1. Register/login and set up a profile.
2. Select a target role and weekly study time.
3. Take a role-specific diagnostic assessment.
4. View calculated competency scores and gaps.
5. Generate a personalized learning plan using the verified scores.
6. Review curated resources and take AI-generated or local-bank practice quizzes.
7. Track tasks and assessment attempts in the Progress page.

### Project structure
```text
SkillPath_AI/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── competencies.csv
│   ├── questions.csv
│   └── resources.csv
├── modules/
│   ├── scoring.py
│   ├── gap_analysis.py
│   ├── simulation.py
│   ├── ai_service.py
│   ├── prompts.py
│   ├── recommendations.py
│   ├── analytics.py
│   └── storage.py
├── utils/
│   ├── auth.py
│   ├── session.py
│   └── ui.py
└── tests/
```

### Run on Windows
Open this folder in VS Code. In Terminal:

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

### Gemini API (optional)
The app works without an API key: learning plans use a rule-based fallback and practice quizzes use the local question bank.

To enable Gemini:
1. Create a Gemini API key.
2. Create `.streamlit/secrets.toml` (this file is ignored by Git).
3. Put this in the file:
```toml
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
```
Do **not** upload the real key to GitHub. An example is available in `secrets.toml.example`.

### Run tests
```powershell
python -m pytest -q
```

### Notes
- The competency dataset and question bank currently focus on **Frontend Developer** and **Data Analyst** roles.
- Skill scores and gap priorities are calculated by Python; AI is only given verified results to create explanations/plans.
- The project uses local CSV files for progress data in this prototype. These generated files and the local account file are excluded from Git.
- The user authentication is a local demo implementation, not production-grade authentication.
- AI-generated content and resource links should be reviewed.

## Role-specific assessment question banks (updated)

The **Select Goal** options are loaded dynamically from `data/competencies.csv`; adding a role there makes it appear automatically. Assessment question banks live in `data/questions/`, with one file per role:

- `frontend_developer.csv`
- `data_analyst.csv`
- `backend_developer.csv`
- `full_stack_developer.csv`
- `devops_engineer.csv`
- `ui_ux_designer.csv`
- `machine_learning_engineer.csv`
- `cloud_architect.csv`
- `cybersecurity_analyst.csv`

Each file uses `question_id,skill_id,difficulty,question,options,correct_answer,explanation`. Difficulty values for new content are `easy`, `hard`, and `advanced`; `medium` remains accepted only for older datasets. Options are separated by `|`, and `correct_answer` is the option letter (`A`–`H`). See `data/questions/README.md` and `data/questions/sample_template.csv`.

The new role banks contain starter/example questions (one per difficulty for each competency). Review and expand these before using the platform for high-stakes assessments.
