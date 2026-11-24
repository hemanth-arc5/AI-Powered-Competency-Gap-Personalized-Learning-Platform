import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from modules.analytics import build_gap_table
from modules.recommendations import recommend_resources


def test_gap_calculation_and_priorities():
    result = build_gap_table([
        {"skill_id": "html", "skill_name": "HTML", "current_score": 85, "target_score": 70},
        {"skill_id": "js", "skill_name": "JavaScript", "current_score": 45, "target_score": 80},
        {"skill_id": "css", "skill_name": "CSS", "current_score": 72, "target_score": 75},
    ])
    assert result.loc[result.skill_id == "html", "gap"].iloc[0] == 0
    assert result.loc[result.skill_id == "js", "priority"].iloc[0] == "High"
    assert result.loc[result.skill_id == "css", "priority"].iloc[0] == "Low"


def test_high_priority_recommended_first():
    resources = pd.DataFrame([
        {"resource_id": "1", "skill_id": "css", "title": "CSS", "url": "https://example.com/css", "level": "Beginner", "type": "Guide", "duration": "1 hour"},
        {"resource_id": "2", "skill_id": "js", "title": "JavaScript", "url": "https://example.com/js", "level": "Beginner", "type": "Guide", "duration": "1 hour"},
    ])
    gaps = [
        {"skill_id": "css", "skill_name": "CSS", "gap": 5, "priority": "Low"},
        {"skill_id": "js", "skill_name": "JavaScript", "gap": 35, "priority": "High"},
    ]
    result = recommend_resources(gaps, resources)
    assert result.iloc[0]["skill_id"] == "js"

if __name__ == "__main__":
    test_gap_calculation_and_priorities()
    test_high_priority_recommended_first()
    print("All Member 4 tests passed.")
