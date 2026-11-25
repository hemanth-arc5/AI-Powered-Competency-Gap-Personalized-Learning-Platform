"""Tests for modules/scoring.py.

Run from the project root with either:
    python -m unittest discover -s tests -v
    python -m pytest -v
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.scoring import (  # noqa: E402
    DataError, SubmissionError, build_answer_key, calculate_skill_scores,
    get_questions_for_skills, get_role_competencies, list_roles, load_competencies,
    load_questions, public_view, validate_submission,
)
from modules.simulation import perfect_submission, simulate_submission, zero_submission  # noqa: E402

DATA = ROOT / "data"


def make_question(qid, skill, correct="A", n_options=4):
    return {"question_id": qid, "skill_id": skill, "difficulty": "easy", "question": f"Question {qid}?",
            "options": [f"opt{i}" for i in range(n_options)], "correct_answer": correct,
            "explanation": "because"}


def write_csv(folder, name, header, rows):
    path = Path(folder) / name
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return path


class RealDataTests(unittest.TestCase):
    """The shipped CSV files must satisfy the project requirements."""

    @classmethod
    def setUpClass(cls):
        cls.competencies = load_competencies(DATA / "competencies.csv")
        cls.questions = load_questions(DATA / "questions.csv")

    def test_two_roles_with_five_to_eight_competencies_each(self):
        roles = list_roles(self.competencies)
        self.assertEqual(roles, ["Frontend Developer", "Data Analyst"])
        for role in roles:
            count = len(get_role_competencies(self.competencies, role))
            self.assertTrue(5 <= count <= 8, f"{role} has {count} competencies")

    def test_every_competency_has_at_least_five_questions_and_mixed_difficulty(self):
        for comp in self.competencies:
            qs = [q for q in self.questions if q["skill_id"] == comp["skill_id"]]
            self.assertGreaterEqual(len(qs), 5, comp["skill_id"])
            self.assertGreaterEqual(len({q["difficulty"] for q in qs}), 2, comp["skill_id"])

    def test_every_question_tag_exists_in_competencies(self):
        known = {c["skill_id"] for c in self.competencies}
        for q in self.questions:
            self.assertIn(q["skill_id"], known, q["question_id"])

    def test_every_question_has_four_options_answer_and_explanation(self):
        for q in self.questions:
            self.assertEqual(len(q["options"]), 4, q["question_id"])
            self.assertIn(q["correct_answer"], "ABCD")
            self.assertTrue(q["explanation"])

    def test_role_lookup_is_case_insensitive_and_unknown_role_raises(self):
        self.assertEqual(len(get_role_competencies(self.competencies, "frontend developer")), 6)
        with self.assertRaises(DataError):
            get_role_competencies(self.competencies, "Astronaut")

    def test_answer_key_is_separate_from_student_view(self):
        view = public_view(self.questions)
        self.assertNotIn("correct_answer", view[0])
        self.assertNotIn("explanation", view[0])
        self.assertEqual(len(build_answer_key(self.questions)), len(self.questions))


class RequiredScenarioTests(unittest.TestCase):
    """Perfect scores, zero scores, missing answers, skills with no questions."""

    @classmethod
    def setUpClass(cls):
        cls.competencies = load_competencies(DATA / "competencies.csv")
        cls.questions = load_questions(DATA / "questions.csv")
        role = get_role_competencies(cls.competencies, "Frontend Developer")
        cls.skill_ids = [c["skill_id"] for c in role]
        cls.fe_questions = get_questions_for_skills(cls.questions, cls.skill_ids)

    def test_perfect_score_gives_100_for_every_skill(self):
        scores = calculate_skill_scores(self.fe_questions, perfect_submission(self.fe_questions), self.skill_ids)
        for skill_id, s in scores.items():
            self.assertEqual(s["score"], 100, skill_id)
            self.assertEqual(s["correct_count"], s["total_count"])
            self.assertEqual(s["status"], "assessed")

    def test_zero_score_is_a_real_zero_not_missing(self):
        scores = calculate_skill_scores(self.fe_questions, zero_submission(self.fe_questions), self.skill_ids)
        for skill_id, s in scores.items():
            self.assertEqual(s["score"], 0, skill_id)
            self.assertEqual(s["correct_count"], 0)
            self.assertEqual(s["status"], "assessed")   # answered, just all wrong

    def test_three_of_five_is_sixty_percent(self):
        sub = simulate_submission(self.fe_questions, {"FE_JS": 3})
        scores = calculate_skill_scores(self.fe_questions, sub, self.skill_ids)
        self.assertEqual(scores["FE_JS"]["score"], 60)
        self.assertEqual((scores["FE_JS"]["correct_count"], scores["FE_JS"]["total_count"]), (3, 5))

    def test_each_possible_score_matches_formula(self):
        for correct in range(6):
            sub = simulate_submission(self.fe_questions, {"FE_HTML": correct})
            score = calculate_skill_scores(self.fe_questions, sub, self.skill_ids)["FE_HTML"]["score"]
            self.assertEqual(score, correct / 5 * 100)

    def test_missing_answers_in_a_skill_count_as_incorrect(self):
        qs = [make_question(f"S_Q{i}", "S") for i in range(1, 5)]   # 4 questions, correct = "A"
        sub = {"S_Q1": "A", "S_Q2": "A", "S_Q3": "B"}               # 2 right, 1 wrong, 1 skipped
        s = calculate_skill_scores(qs, sub, ["S"])["S"]
        self.assertEqual((s["correct_count"], s["answered_count"], s["total_count"]), (2, 3, 4))
        self.assertEqual(s["score"], 50)

    def test_skill_with_no_answers_is_not_attempted_not_zero(self):
        sub = simulate_submission(self.fe_questions, {s: 5 for s in self.skill_ids}, skip_skills=("FE_GIT",))
        scores = calculate_skill_scores(self.fe_questions, sub, self.skill_ids)
        self.assertIsNone(scores["FE_GIT"]["score"])
        self.assertEqual(scores["FE_GIT"]["status"], "not_attempted")
        self.assertEqual(scores["FE_HTML"]["score"], 100)   # other skills unaffected

    def test_blank_answers_are_treated_as_unanswered(self):
        qs = [make_question("S_Q1", "S"), make_question("S_Q2", "S")]
        s = calculate_skill_scores(qs, {"S_Q1": "A", "S_Q2": ""}, ["S"])["S"]
        self.assertEqual((s["answered_count"], s["score"]), (1, 50))
        s = calculate_skill_scores(qs, {"S_Q1": None, "S_Q2": "  "}, ["S"])["S"]
        self.assertIsNone(s["score"])

    def test_skill_with_no_questions_is_flagged_and_does_not_vanish(self):
        qs = [make_question("S_Q1", "S")]
        scores = calculate_skill_scores(qs, {"S_Q1": "A"}, ["S", "EMPTY"])
        self.assertEqual(scores["S"]["score"], 100)
        self.assertIsNone(scores["EMPTY"]["score"])
        self.assertEqual(scores["EMPTY"]["status"], "no_questions")
        self.assertEqual(scores["EMPTY"]["total_count"], 0)

    def test_changing_answers_changes_the_score(self):
        low = simulate_submission(self.fe_questions, {"FE_JS": 1})
        high = simulate_submission(self.fe_questions, {"FE_JS": 4})
        s_low = calculate_skill_scores(self.fe_questions, low, self.skill_ids)["FE_JS"]["score"]
        s_high = calculate_skill_scores(self.fe_questions, high, self.skill_ids)["FE_JS"]["score"]
        self.assertEqual((s_low, s_high), (20, 80))


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.qs = [make_question("Q1", "S"), make_question("Q2", "S", correct="C")]

    def test_valid_submission_is_normalised(self):
        r = validate_submission({"Q1": " a ", "Q2": "c"}, self.qs)
        self.assertTrue(r.valid)
        self.assertEqual(r.cleaned, {"Q1": "A", "Q2": "C"})
        self.assertEqual(r.warnings, [])

    def test_unknown_question_id_is_an_error(self):
        r = validate_submission({"Q1": "A", "NOPE": "A"}, self.qs)
        self.assertFalse(r.valid)
        self.assertIn("NOPE", r.errors[0])

    def test_option_outside_range_is_an_error(self):
        r = validate_submission({"Q1": "E"}, self.qs)      # only A-D exist
        self.assertFalse(r.valid)
        r = validate_submission({"Q1": "1"}, self.qs)
        self.assertFalse(r.valid)

    def test_non_string_answer_is_an_error(self):
        self.assertFalse(validate_submission({"Q1": 3}, self.qs).valid)

    def test_empty_or_wrong_type_submission_is_an_error(self):
        self.assertFalse(validate_submission({}, self.qs).valid)
        self.assertFalse(validate_submission(["A", "B"], self.qs).valid)
        self.assertFalse(validate_submission(None, self.qs).valid)

    def test_unanswered_questions_give_a_warning_not_an_error(self):
        r = validate_submission({"Q1": "A"}, self.qs)
        self.assertTrue(r.valid)
        self.assertEqual(len(r.warnings), 1)
        self.assertIn("Q2", r.warnings[0])

    def test_scoring_an_invalid_submission_raises(self):
        with self.assertRaises(SubmissionError):
            calculate_skill_scores(self.qs, {"Q1": "Z"})


class LoaderErrorTests(unittest.TestCase):
    """Malformed data files must fail loudly instead of producing wrong scores."""

    Q_HEADER = ["question_id", "skill_id", "difficulty", "question", "options", "correct_answer", "explanation"]
    C_HEADER = ["skill_id", "role", "skill_name", "target_score", "prerequisites"]

    def q_row(self, **override):
        row = {"question_id": "Q1", "skill_id": "S", "difficulty": "easy", "question": "Q?",
               "options": "a|b|c|d", "correct_answer": "B", "explanation": "why"}
        row.update(override)
        return [row[h] for h in self.Q_HEADER]

    def load_q(self, rows, header=None):
        with tempfile.TemporaryDirectory() as tmp:
            return load_questions(write_csv(tmp, "q.csv", header or self.Q_HEADER, rows))

    def load_c(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            return load_competencies(write_csv(tmp, "c.csv", self.C_HEADER, rows))

    def test_good_row_loads(self):
        q = self.load_q([self.q_row()])[0]
        self.assertEqual(q["options"], ["a", "b", "c", "d"])
        self.assertEqual(q["correct_answer"], "B")

    def test_bad_questions_are_rejected(self):
        cases = {
            "answer outside options": self.q_row(correct_answer="E"),
            "bad difficulty": self.q_row(difficulty="impossible"),
            "one option only": self.q_row(options="a"),
            "duplicate options": self.q_row(options="a|a|b|c"),
            "empty explanation": self.q_row(explanation=""),
            "empty id": self.q_row(question_id=""),
        }
        for name, row in cases.items():
            with self.subTest(name), self.assertRaises(DataError):
                self.load_q([row])

    def test_duplicate_question_id_is_rejected(self):
        with self.assertRaises(DataError):
            self.load_q([self.q_row(), self.q_row()])

    def test_missing_column_is_rejected(self):
        with self.assertRaises(DataError):
            self.load_q([["Q1", "S", "easy", "Q?", "a|b", "A"]], header=self.Q_HEADER[:-1])

    def test_bad_competency_rows_are_rejected(self):
        cases = {
            "target above 100": [["A", "R", "A", "150", ""]],
            "target not a number": [["A", "R", "A", "high", ""]],
            "duplicate skill_id": [["A", "R", "A", "50", ""], ["A", "R", "B", "50", ""]],
            "unknown prerequisite": [["A", "R", "A", "50", "GHOST"]],
            "self prerequisite": [["A", "R", "A", "50", "A"]],
            "prerequisite cycle": [["A", "R", "A", "50", "B"], ["B", "R", "B", "50", "A"]],
        }
        for name, rows in cases.items():
            with self.subTest(name), self.assertRaises(DataError):
                self.load_c(rows)

    def test_prerequisites_are_parsed_into_a_list(self):
        comps = self.load_c([["A", "R", "A", "50", ""], ["B", "R", "B", "60", "A"], ["C", "R", "C", "70", "A|B"]])
        self.assertEqual([c["prerequisites"] for c in comps], [[], ["A"], ["A", "B"]])
        self.assertEqual(comps[1]["target_score"], 60.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
