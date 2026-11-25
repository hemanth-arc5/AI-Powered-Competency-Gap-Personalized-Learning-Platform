"""Prompt templates. Scores are trusted inputs. The model never calculates them."""
import json

PLAN_TEMPLATE = """You are a learning-path assistant. Create a realistic learning plan using only the information below.

Goal: {target_role}
Available study time: {hours_per_week} hours per week
Verified competency results (calculated by the system, trusted): {skill_scores}
Approved learning resources: {resources}

Instructions:
1. Do not invent, change, or recalculate assessment scores.
2. Prioritize High gaps first, then Medium. Skip skills with gap 0.
3. Respect prerequisites: {prerequisites}
4. Use resources only from the approved list. Refer to them by resource_id. If none fits, set resource_id to null.
5. Each week's total estimated_minutes must not exceed {max_minutes}.
6. Each week needs one short checkpoint task.
7. Return ONLY valid JSON in this exact shape:
{{
  "summary": "2-3 sentences on strongest skills and biggest gaps",
  "weeks": [
    {{
      "week": 1,
      "skill_id": "string",
      "topic": "string",
      "objective": "string",
      "activity": "string",
      "resource_id": "string or null",
      "estimated_minutes": 120,
      "checkpoint": "string"
    }}
  ],
  "disclaimer": "Recommendations are guidance. Verify resource links."
}}
"""

QUIZ_TEMPLATE = """You are a quiz generator. Create {n} multiple-choice questions.

Skill: {skill_name}
Role context: {target_role}
Difficulty: {difficulty}

Rules:
1. Each question has exactly 4 options.
2. Exactly one option is correct.
3. correct_answer must be the exact text of one option.
4. Give a one-sentence explanation.
5. Do not repeat questions. Stay within the skill.
6. Return ONLY valid JSON in this exact shape:
{{
  "questions": [
    {{
      "question": "string",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "string",
      "explanation": "string"
    }}
  ]
}}
"""


def plan_prompt(target_role, hours_per_week, skill_scores, resources, prerequisites):
    return PLAN_TEMPLATE.format(
        target_role=target_role,
        hours_per_week=hours_per_week,
        skill_scores=json.dumps(skill_scores, indent=1),
        resources=json.dumps(resources, indent=1),
        prerequisites=json.dumps(prerequisites) if prerequisites else "none defined",
        max_minutes=int(hours_per_week * 60),
    )


def quiz_prompt(skill_name, difficulty, n, target_role=""):
    return QUIZ_TEMPLATE.format(
        skill_name=skill_name, difficulty=difficulty, n=n,
        target_role=target_role or "general",
    )