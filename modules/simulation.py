"""Builds fictional student submissions for demos and tests (no real student data).

simulate_submission(questions, correct_per_skill) answers the first N questions of each
skill correctly and the rest wrongly, so the expected score is known in advance:
    N correct out of 5  ->  N * 20 %
"""
from modules.scoring import LETTERS


def _wrong_letter(question):
    for letter in LETTERS[:len(question["options"])]:
        if letter != question["correct_answer"]:
            return letter
    raise ValueError("question has a single option")


def simulate_submission(questions, correct_per_skill, skip_skills=()):
    """correct_per_skill: {skill_id: number of questions to answer correctly}.
    Skills missing from the dict are answered entirely wrong.  Skills in skip_skills are not answered at all."""
    submission = {}
    seen = {}
    for q in questions:
        skill = q["skill_id"]
        if skill in skip_skills:
            continue
        index = seen.get(skill, 0)
        seen[skill] = index + 1
        right = index < correct_per_skill.get(skill, 0)
        submission[q["question_id"]] = q["correct_answer"] if right else _wrong_letter(q)
    return submission


def perfect_submission(questions):
    return {q["question_id"]: q["correct_answer"] for q in questions}


def zero_submission(questions):
    return {q["question_id"]: _wrong_letter(q) for q in questions}
