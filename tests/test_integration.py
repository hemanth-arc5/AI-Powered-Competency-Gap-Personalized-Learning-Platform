from pathlib import Path
import pandas as pd
from modules.scoring import load_competencies, load_questions, get_role_competencies, get_questions_for_skills
from modules.simulation import simulate_submission
from modules.gap_analysis import generate_gap_report
from modules.recommendations import load_resources, recommend_resources
from modules.ai_service import generate_learning_plan

ROOT = Path(__file__).resolve().parents[1]

def test_end_to_end_frontend_pipeline():
    competencies = load_competencies(ROOT / "data" / "competencies.csv")
    questions = load_questions(ROOT / "data" / "questions.csv")
    role = "Frontend Developer"
    role_comps = get_role_competencies(competencies, role)
    role_questions = get_questions_for_skills(questions, [c["skill_id"] for c in role_comps])
    submission = simulate_submission(role_questions, {"FE_HTML": 4, "FE_CSS": 3, "FE_JS": 1, "FE_RESP": 2, "FE_GIT": 1, "FE_REACT": 2})
    report = generate_gap_report(role, submission, questions, competencies)
    assert report["valid"]
    assert len(report["rows"]) == len(role_comps)
    assert report["rows"][0]["priority"] == "High"
    resources = load_resources(ROOT / "data" / "resources.csv")
    recommendations = recommend_resources(pd.DataFrame(report["rows"]), resources)
    assert not recommendations.empty
    scores = [{"skill_id":r["skill_id"],"skill_name":r["skill_name"],"current":r["current"],"target":r["target"],"gap":r["gap"] or 0,"priority":r["priority"]} for r in report["rows"]]
    ai_resources = resources.to_dict("records")
    for item in ai_resources:
        try:
            item["duration"] = int(float(str(item["duration"]).split()[0]) * 60) if "hour" in str(item["duration"]).lower() else int(float(str(item["duration"]).split()[0]))
        except Exception:
            item["duration"] = 120
    plan = generate_learning_plan(role, 5, scores, ai_resources)
    assert plan["ok"] and plan["data"] and plan["source"] in ("ai", "fallback")
