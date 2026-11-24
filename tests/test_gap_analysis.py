"""Tests for modules/gap_analysis.py.

Run from the project root with either:
    python -m unittest discover -s tests -v
    python -m pytest -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.gap_analysis import (  # noqa: E402
    build_gap_rows, calculate_gap, compare_gaps, explain_gap, export_gap_report_csv,
    format_gap_report, generate_gap_report, priority_label, sort_gaps, summarize_gaps,
)
from modules.scoring import get_role_competencies, load_competencies, load_questions  # noqa: E402
from modules.simulation import perfect_submission, simulate_submission, zero_submission  # noqa: E402

DATA = ROOT / "data"


class FormulaTests(unittest.TestCase):
    def test_gap_formula_examples_from_the_project_guide(self):
        cases = [
            (80, 45, 35),   # JavaScript: target 80, scored 45 -> 35 points short
            (70, 85, 0),    # HTML: target 70, scored 85 -> target exceeded, gap is 0 (never negative)
            (75, 75, 0),    # exactly on target
            (65, 30, 35),   # Git
            (70, 0, 70),    # zero score -> gap equals the target
            (70, 100, 0),   # perfect score
        ]
        for target, current, expected in cases:
            with self.subTest(target=target, current=current):
                self.assertEqual(calculate_gap(target, current), expected)

    def test_gap_is_never_negative(self):
        for current in range(0, 101, 5):
            self.assertGreaterEqual(calculate_gap(60, current), 0)

    def test_no_score_means_no_gap(self):
        self.assertIsNone(calculate_gap(80, None))

    def test_out_of_range_values_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_gap(120, 50)
        with self.assertRaises(ValueError):
            calculate_gap(80, -5)
        with self.assertRaises(ValueError):
            calculate_gap(80, 101)

    def test_priority_thresholds(self):
        cases = [(0, "Strong"), (0.5, "Low"), (1, "Low"), (10, "Low"), (10.01, "Medium"), (11, "Medium"),
                 (25, "Medium"), (25.01, "High"), (26, "High"), (100, "High"), (None, "Not Assessed")]
        for gap, expected in cases:
            with self.subTest(gap=gap):
                self.assertEqual(priority_label(gap), expected)

    def test_negative_gap_to_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            priority_label(-1)


class SortingTests(unittest.TestCase):
    @staticmethod
    def row(name, gap, target=70):
        return {"skill_name": name, "gap": gap, "target": target}

    def test_sorted_from_biggest_gap_to_smallest(self):
        rows = sort_gaps([self.row("A", 5), self.row("B", 40), self.row("C", 0), self.row("D", 20)])
        self.assertEqual([r["skill_name"] for r in rows], ["B", "D", "A", "C"])

    def test_ties_are_broken_by_higher_target_then_name(self):
        rows = sort_gaps([self.row("Zeta", 20, 60), self.row("Beta", 20, 80), self.row("Alpha", 20, 80)])
        self.assertEqual([r["skill_name"] for r in rows], ["Alpha", "Beta", "Zeta"])

    def test_not_assessed_skills_go_last(self):
        rows = sort_gaps([self.row("X", None), self.row("A", 0), self.row("B", 30)])
        self.assertEqual([r["skill_name"] for r in rows], ["B", "A", "X"])


class FullReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.competencies = load_competencies(DATA / "competencies.csv")
        cls.questions = load_questions(DATA / "questions.csv")

    def report(self, role, submission, questions=None):
        return generate_gap_report(role, submission, questions or self.questions, self.competencies)

    def role_questions(self, role):
        ids = {c["skill_id"] for c in get_role_competencies(self.competencies, role)}
        return [q for q in self.questions if q["skill_id"] in ids]

    # ---- the four required scenarios --------------------------------------
    def test_perfect_scores_leave_no_gaps_in_either_role(self):
        for role in ("Frontend Developer", "Data Analyst"):
            with self.subTest(role=role):
                rq = self.role_questions(role)
                result = self.report(role, perfect_submission(rq))
                self.assertTrue(result["valid"])
                for row in result["rows"]:
                    self.assertEqual(row["current"], 100)
                    self.assertEqual(row["gap"], 0)
                    self.assertEqual(row["priority"], "Strong")
                self.assertEqual(result["summary"]["counts"]["High"], 0)
                self.assertIsNone(result["summary"]["biggest_gap"])

    def test_zero_scores_make_every_gap_equal_to_its_target(self):
        rq = self.role_questions("Frontend Developer")
        result = self.report("Frontend Developer", zero_submission(rq))
        for row in result["rows"]:
            self.assertEqual(row["current"], 0)
            self.assertEqual(row["gap"], row["target"])
            self.assertEqual(row["priority"], "High")
        # highest target first: JavaScript (80) leads, Git (65) is last
        self.assertEqual(result["rows"][0]["skill_name"], "JavaScript")
        self.assertEqual(result["rows"][-1]["skill_name"], "Git")

    def test_missing_answers_for_a_skill_marks_it_not_assessed(self):
        rq = self.role_questions("Frontend Developer")
        sub = simulate_submission(rq, {s["skill_id"]: 5 for s in rq}, skip_skills=("FE_GIT",))
        result = self.report("Frontend Developer", sub)
        git = next(r for r in result["rows"] if r["skill_id"] == "FE_GIT")
        self.assertIsNone(git["current"])
        self.assertIsNone(git["gap"])
        self.assertEqual(git["priority"], "Not Assessed")
        self.assertEqual(result["rows"][-1]["skill_id"], "FE_GIT")          # sorted to the bottom
        self.assertEqual(result["summary"]["not_assessed"], ["Git"])
        self.assertEqual(result["summary"]["counts"]["Not Assessed"], 1)

    def test_skill_with_no_questions_is_reported_not_hidden(self):
        questions = [q for q in self.questions if q["skill_id"] != "FE_REACT"]   # remove every React question
        rq = [q for q in questions if q["skill_id"].startswith("FE_")]
        result = self.report("Frontend Developer", perfect_submission(rq), questions)
        react = next(r for r in result["rows"] if r["skill_id"] == "FE_REACT")
        self.assertEqual(react["status"], "no_questions")
        self.assertIsNone(react["gap"])
        self.assertEqual(react["priority"], "Not Assessed")
        self.assertEqual(len(result["rows"]), 6)    # still one row per competency

    # ---- invalid input ------------------------------------------------------
    def test_invalid_submission_returns_errors_and_no_rows(self):
        result = self.report("Frontend Developer", {"FE_HTML_Q01": "Z"})
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"])
        self.assertEqual(result["rows"], [])

    def test_answers_from_another_role_are_rejected(self):
        result = self.report("Frontend Developer", {"DA_SQL_Q01": "A"})
        self.assertFalse(result["valid"])

    def test_empty_submission_is_rejected(self):
        self.assertFalse(self.report("Frontend Developer", {})["valid"])

    # ---- the viva scenario: JavaScript vs HTML -------------------------------
    def test_javascript_is_a_bigger_gap_than_html(self):
        rq = self.role_questions("Frontend Developer")
        # HTML 3/5 = 60 (target 70) ; JavaScript 2/5 = 40 (target 80)
        sub = simulate_submission(rq, {"FE_HTML": 3, "FE_JS": 2, "FE_CSS": 4, "FE_RESP": 3, "FE_GIT": 1, "FE_REACT": 2})
        result = self.report("Frontend Developer", sub)
        rows = {r["skill_name"]: r for r in result["rows"]}
        js, html = rows["JavaScript"], rows["HTML"]
        self.assertEqual((js["current"], js["target"], js["gap"], js["priority"]), (40, 80, 40, "High"))
        self.assertEqual((html["current"], html["target"], html["gap"], html["priority"]), (60, 70, 10, "Low"))
        self.assertGreater(js["gap"], html["gap"])
        order = [r["skill_name"] for r in result["rows"]]
        self.assertLess(order.index("JavaScript"), order.index("HTML"))
        text = compare_gaps(result["rows"], "JavaScript", "HTML")
        self.assertIn("JavaScript is a bigger gap than HTML", text)
        self.assertIn("max(0, 80 - 40) = 40", text)
        self.assertIn("max(0, 70 - 60) = 10", text)

    def test_changing_answers_changes_gaps_and_order(self):
        rq = self.role_questions("Frontend Developer")
        base = {s: 3 for s in ("FE_HTML", "FE_CSS", "FE_JS", "FE_RESP", "FE_GIT", "FE_REACT")}
        before = self.report("Frontend Developer", simulate_submission(rq, base))
        improved = dict(base, FE_JS=5)
        after = self.report("Frontend Developer", simulate_submission(rq, improved))
        js_before = next(r for r in before["rows"] if r["skill_id"] == "FE_JS")
        js_after = next(r for r in after["rows"] if r["skill_id"] == "FE_JS")
        self.assertEqual((js_before["gap"], js_after["gap"]), (20, 0))
        self.assertEqual(js_after["priority"], "Strong")

    def test_prerequisite_with_a_big_gap_is_flagged_learn_first(self):
        rq = self.role_questions("Frontend Developer")
        sub = simulate_submission(rq, {"FE_HTML": 5, "FE_CSS": 5, "FE_JS": 1, "FE_RESP": 5, "FE_GIT": 5, "FE_REACT": 3})
        rows = {r["skill_id"]: r for r in self.report("Frontend Developer", sub)["rows"]}
        self.assertEqual(rows["FE_REACT"]["learn_first"], ["FE_JS"])   # React needs JavaScript, which is weak
        self.assertEqual(rows["FE_JS"]["learn_first"], [])             # HTML is strong, nothing blocks JS

    # ---- output helpers -----------------------------------------------------
    def test_text_report_and_csv_export(self):
        rq = self.role_questions("Data Analyst")
        sub = simulate_submission(rq, {s["skill_id"]: 2 for s in rq})
        result = self.report("Data Analyst", sub)
        text = format_gap_report(result["rows"], "Data Analyst")
        self.assertIn("gap = max(0, target - current)", text)
        self.assertIn("SQL", text)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.csv"
            export_gap_report_csv(result["rows"], path)
            lines = path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1 + len(result["rows"]))
        self.assertTrue(lines[0].startswith("rank,skill_id"))

    def test_explain_gap_mentions_formula_and_priority(self):
        rows = build_gap_rows(
            {"X": {"score": 45.0, "status": "assessed"}},
            [{"skill_id": "X", "skill_name": "JavaScript", "role": "R", "target_score": 80.0, "prerequisites": []}])
        text = explain_gap(rows[0])
        self.assertIn("max(0, 80 - 45) = 35", text)
        self.assertIn("High", text)

    def test_summary_counts_add_up(self):
        rq = self.role_questions("Frontend Developer")
        result = self.report("Frontend Developer", simulate_submission(rq, {"FE_HTML": 5, "FE_JS": 2, "FE_GIT": 0}))
        s = summarize_gaps(result["rows"])
        self.assertEqual(sum(s["counts"].values()), s["total_skills"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
