"""Scoring module (Member 2).

Loads the competency framework and the question bank, validates a student's
submission and calculates a 0-100 score for every skill.

Scoring rule (easy to explain in the viva):

    score = (correct answers / total questions for the skill) * 100

Edge-case rules (these are project decisions, written down on purpose):
  * A question the student skipped counts as INCORRECT, but only if the student
    answered at least one question of that skill.
  * If the student answered NO question of a skill, the skill is "not_attempted"
    and its score is None.  It is never silently treated as 0 or 100.
  * If the question bank has NO question for a skill, the status is "no_questions"
    and the score is None.

Everything here is plain Python (no AI): the same input always gives the same score.
"""
import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

LETTERS = "ABCDEFGH"
OPTION_SEPARATOR = "|"
VALID_DIFFICULTIES = ("easy", "medium", "hard")

COMPETENCY_COLUMNS = ["skill_id", "role", "skill_name", "target_score", "prerequisites"]
QUESTION_COLUMNS = ["question_id", "skill_id", "difficulty", "question",
                    "options", "correct_answer", "explanation"]

# Status values stored in every per-skill result
STATUS_ASSESSED = "assessed"
STATUS_NOT_ATTEMPTED = "not_attempted"   # questions exist, student answered none
STATUS_NO_QUESTIONS = "no_questions"     # question bank has nothing for this skill


class DataError(ValueError):
    """The competency or question files are malformed."""


class SubmissionError(ValueError):
    """A student's submission is invalid and cannot be scored."""


@dataclass
class ValidationResult:
    valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    cleaned: dict = field(default_factory=dict)   # {question_id: "A".."H"} (valid, normalised answers only)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _read_csv(path, required_columns):
    path = Path(path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in required_columns if c not in (reader.fieldnames or [])]
        if missing:
            raise DataError(f"{path.name}: missing column(s) {missing}")
        return list(reader)


def _split(value):
    return [part.strip() for part in (value or "").split(OPTION_SEPARATOR) if part.strip()]


def load_competencies(path):
    """Return a list of competency dicts:
    {skill_id, role, skill_name, target_score (float), prerequisites (list of skill_ids)}.
    """
    competencies = []
    seen = set()
    for line_no, row in enumerate(_read_csv(path, COMPETENCY_COLUMNS), start=2):
        skill_id = row["skill_id"].strip()
        if not skill_id:
            raise DataError(f"competencies line {line_no}: empty skill_id")
        if skill_id in seen:
            raise DataError(f"competencies line {line_no}: duplicate skill_id '{skill_id}'")
        seen.add(skill_id)
        try:
            target = float(row["target_score"])
        except ValueError:
            raise DataError(f"competencies line {line_no}: target_score '{row['target_score']}' is not a number")
        if not 0 <= target <= 100:
            raise DataError(f"competencies line {line_no}: target_score {target:g} must be between 0 and 100")
        competencies.append({
            "skill_id": skill_id,
            "role": row["role"].strip(),
            "skill_name": row["skill_name"].strip(),
            "target_score": target,
            "prerequisites": _split(row["prerequisites"]),
        })
    _check_prerequisites(competencies)
    return competencies


def _check_prerequisites(competencies):
    """Every prerequisite must exist, must not be the skill itself, and there must be no cycle."""
    ids = {c["skill_id"] for c in competencies}
    graph = {c["skill_id"]: c["prerequisites"] for c in competencies}
    for skill_id, prereqs in graph.items():
        for p in prereqs:
            if p == skill_id:
                raise DataError(f"'{skill_id}' lists itself as a prerequisite")
            if p not in ids:
                raise DataError(f"'{skill_id}' has unknown prerequisite '{p}'")
    # cycle detection (depth-first search with a "currently visiting" set)
    done, visiting = set(), set()

    def visit(node):
        if node in done:
            return
        if node in visiting:
            raise DataError(f"prerequisite cycle detected at '{node}'")
        visiting.add(node)
        for p in graph[node]:
            visit(p)
        visiting.discard(node)
        done.add(node)

    for node in graph:
        visit(node)


def list_roles(competencies):
    """Role names in the order they first appear."""
    return list(dict.fromkeys(c["role"] for c in competencies))


def get_role_competencies(competencies, role):
    """All competencies of one role (case-insensitive). Raises DataError for an unknown role."""
    selected = [c for c in competencies if c["role"].lower() == str(role).strip().lower()]
    if not selected:
        raise DataError(f"Unknown role '{role}'. Available roles: {list_roles(competencies)}")
    return selected


def load_questions(path):
    """Return a list of question dicts:
    {question_id, skill_id, difficulty, question, options (list), correct_answer (letter), explanation}.
    Raises DataError if any question is malformed.
    """
    questions = []
    seen = set()
    for line_no, row in enumerate(_read_csv(path, QUESTION_COLUMNS), start=2):
        qid = row["question_id"].strip()
        where = f"questions line {line_no} ({qid or 'no id'})"
        if not qid:
            raise DataError(f"{where}: empty question_id")
        if qid in seen:
            raise DataError(f"{where}: duplicate question_id")
        seen.add(qid)
        if not row["skill_id"].strip():
            raise DataError(f"{where}: empty skill_id")
        difficulty = row["difficulty"].strip().lower()
        if difficulty not in VALID_DIFFICULTIES:
            raise DataError(f"{where}: difficulty '{row['difficulty']}' must be one of {VALID_DIFFICULTIES}")
        if not row["question"].strip():
            raise DataError(f"{where}: empty question text")
        options = _split(row["options"])
        if not 2 <= len(options) <= len(LETTERS):
            raise DataError(f"{where}: needs between 2 and {len(LETTERS)} options, found {len(options)}")
        if len(set(options)) != len(options):
            raise DataError(f"{where}: duplicate options")
        answer = row["correct_answer"].strip().upper()
        if answer not in LETTERS[:len(options)]:
            raise DataError(f"{where}: correct_answer '{row['correct_answer']}' is not one of {LETTERS[:len(options)]}")
        if not row["explanation"].strip():
            raise DataError(f"{where}: empty explanation")
        questions.append({
            "question_id": qid,
            "skill_id": row["skill_id"].strip(),
            "difficulty": difficulty,
            "question": row["question"].strip(),
            "options": options,
            "correct_answer": answer,
            "explanation": row["explanation"].strip(),
        })
    return questions


def get_questions_for_skills(questions, skill_ids):
    """Questions whose skill tag is in skill_ids (keeps the original order)."""
    wanted = set(skill_ids)
    return [q for q in questions if q["skill_id"] in wanted]


def build_answer_key(questions):
    """{question_id: correct letter}. Kept separate from the question text."""
    return {q["question_id"]: q["correct_answer"] for q in questions}


def public_view(questions):
    """Questions safe to show a student: the answer and explanation are removed."""
    return [{k: v for k, v in q.items() if k not in ("correct_answer", "explanation")} for q in questions]


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate_submission(submission, questions):
    """Check a submission {question_id: chosen letter} against the questions of this assessment.

    Errors (submission cannot be scored):
      * not a dict, or contains no answers at all
      * unknown question_id (not part of this assessment)
      * answer that is not a letter of a real option for that question
    Warnings (still scorable):
      * blank / None answers and questions missing from the submission (counted as unanswered)

    Answers are normalised: " b " -> "B".
    """
    errors, warnings, cleaned = [], [], {}
    if not isinstance(submission, dict):
        return ValidationResult(False, ["Submission must be a dict of {question_id: answer}."], [], {})

    by_id = {q["question_id"]: q for q in questions}
    for qid, raw in submission.items():
        question = by_id.get(qid)
        if question is None:
            errors.append(f"Unknown question_id '{qid}' (not part of this assessment).")
            continue
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue  # blank = unanswered, reported below
        if not isinstance(raw, str):
            errors.append(f"Answer for {qid} must be a letter such as 'A', got {raw!r}.")
            continue
        letter = raw.strip().upper()
        valid_letters = LETTERS[:len(question["options"])]
        if letter not in valid_letters:
            errors.append(f"Invalid option '{raw}' for {qid}; choose one of {', '.join(valid_letters)}.")
            continue
        cleaned[qid] = letter

    if not submission:
        errors.append("Submission contains no answers.")

    unanswered = sorted(set(by_id) - set(cleaned))
    if unanswered and not errors:
        warnings.append(f"{len(unanswered)} question(s) unanswered: {', '.join(unanswered)}")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings, cleaned=cleaned)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def calculate_skill_scores(questions, submission, skill_ids=None):
    """Per-skill scores.

    questions  : the questions of this assessment (use get_questions_for_skills for one role)
    submission : {question_id: letter}
    skill_ids  : skills to report; pass the role's skills so that a skill with no
                 questions still shows up (as "no_questions") instead of vanishing.
                 Default: every skill that has questions.

    Returns {skill_id: {skill_id, correct_count, answered_count, total_count, score, status}}
    Raises SubmissionError if the submission is invalid.
    """
    result = validate_submission(submission, questions)
    if not result.valid:
        raise SubmissionError(" ".join(result.errors))
    answers = result.cleaned

    by_skill = defaultdict(list)
    for q in questions:
        by_skill[q["skill_id"]].append(q)
    if skill_ids is None:
        skill_ids = sorted(by_skill)

    scores = {}
    for skill_id in skill_ids:
        skill_questions = by_skill.get(skill_id, [])
        total = len(skill_questions)
        answered = sum(1 for q in skill_questions if q["question_id"] in answers)
        correct = sum(1 for q in skill_questions if answers.get(q["question_id"]) == q["correct_answer"])
        if total == 0:
            score, status = None, STATUS_NO_QUESTIONS
        elif answered == 0:
            score, status = None, STATUS_NOT_ATTEMPTED
        else:
            score, status = round(correct / total * 100, 2), STATUS_ASSESSED
        scores[skill_id] = {
            "skill_id": skill_id,
            "correct_count": correct,
            "answered_count": answered,
            "total_count": total,
            "score": score,
            "status": status,
        }
    return scores
