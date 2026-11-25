import pytest
from modules import ai_service as ai

SCORES = [
    {"skill_id": "js", "skill_name": "JavaScript", "current": 45, "target": 80, "gap": 35, "priority": "High"},
    {"skill_id": "git", "skill_name": "Git", "current": 30, "target": 65, "gap": 35, "priority": "High"},
    {"skill_id": "html", "skill_name": "HTML", "current": 85, "target": 70, "gap": 0, "priority": "Low"},
]
RES = [
    {"resource_id": "r1", "skill_id": "js", "title": "JS Basics", "url": "https://example.com", "level": "beginner", "type": "video", "duration": 90},
]
GOOD_PLAN = {"summary": "x", "weeks": [{"week": 1, "skill_id": "js", "topic": "JS", "objective": "o",
             "activity": "a", "resource_id": "r1", "estimated_minutes": 120, "checkpoint": "c"}]}


def test_missing_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(ai, "get_api_key", lambda: None)
    r = ai.generate_learning_plan("Frontend Developer", 5, SCORES, RES)
    assert r["ok"] and r["source"] == "fallback" and r["error"]


def test_good_plan(monkeypatch):
    monkeypatch.setattr(ai, "_call_llm", lambda p: dict(GOOD_PLAN))
    r = ai.generate_learning_plan("Frontend Developer", 5, SCORES, RES)
    assert r["source"] == "ai"


def test_invented_resource_removed():
    plan = {**GOOD_PLAN, "weeks": [{**GOOD_PLAN["weeks"][0], "resource_id": "fake"}]}
    out = ai.validate_plan(plan, RES, 5)
    assert out["weeks"][0]["resource_id"] is None


def test_plan_exceeds_time():
    plan = {**GOOD_PLAN, "weeks": [{**GOOD_PLAN["weeks"][0], "estimated_minutes": 9999}]}
    with pytest.raises(ai.AIError):
        ai.validate_plan(plan, RES, 5)


def test_fallback_skips_zero_gap():
    plan = ai.fallback_plan("X", 5, SCORES, RES)
    assert [w["skill_id"] for w in plan["weeks"]] == ["js", "git"]


def test_changing_hours_changes_prompt():
    from modules.prompts import plan_prompt
    assert plan_prompt("X", 3, SCORES, RES, None) != plan_prompt("X", 10, SCORES, RES, None)


def test_question_validation():
    bad = {"questions": [{"question": "q", "options": ["a", "b", "c", "d"], "correct_answer": "z", "explanation": "e"}]}
    with pytest.raises(ai.AIError):
        ai.validate_questions(bad, 5)


def test_quiz_failure_returns_error(monkeypatch):
    def boom(p): raise ai.AIError("quota")
    monkeypatch.setattr(ai, "_call_llm", boom)
    r = ai.generate_practice_questions("Git")
    assert not r["ok"] and r["error"] == "quota"