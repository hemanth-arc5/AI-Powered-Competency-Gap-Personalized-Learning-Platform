"""Viva demo (Member 2): "How does the system know JavaScript is a bigger gap than HTML?"

Run:  python demo_viva.py

Uses a FICTIONAL student for the Frontend Developer role.  Every number printed below
comes from the same functions the Streamlit app will call - no AI is involved in scoring.
"""
from pathlib import Path

from modules.gap_analysis import (compare_gaps, explain_gap, export_gap_report_csv,
                                  format_gap_report, generate_gap_report)
from modules.scoring import (get_questions_for_skills, get_role_competencies,
                             load_competencies, load_questions)
from modules.simulation import simulate_submission

ROOT = Path(__file__).resolve().parent
ROLE = "Frontend Developer"

# Fictional student: how many of the 5 questions of each skill were answered correctly.
CORRECT_PER_SKILL = {"FE_HTML": 3, "FE_CSS": 4, "FE_JS": 2, "FE_RESP": 3, "FE_GIT": 1, "FE_REACT": 2}


def heading(text):
    print("\n" + "=" * 78 + f"\n{text}\n" + "=" * 78)


def main():
    competencies = load_competencies(ROOT / "data" / "competencies.csv")
    questions = load_questions(ROOT / "data" / "questions.csv")
    role_comps = get_role_competencies(competencies, ROLE)
    role_questions = get_questions_for_skills(questions, [c["skill_id"] for c in role_comps])

    heading(f"STEP 1 - Competencies and target scores for {ROLE}")
    for c in role_comps:
        prereq = ", ".join(c["prerequisites"]) or "none"
        print(f"  {c['skill_id']:<9}{c['skill_name']:<20} target = {c['target_score']:g}   prerequisites: {prereq}")
    print(f"\n  Question bank for this role: {len(role_questions)} questions "
          f"({len(role_questions) // len(role_comps)} per skill)")

    heading("STEP 2 - Student answers (fictional) -> per-skill score")
    submission = simulate_submission(role_questions, CORRECT_PER_SKILL)
    result = generate_gap_report(ROLE, submission, questions, competencies)
    print("  score = correct / total * 100\n")
    for c in role_comps:
        s = result["skill_scores"][c["skill_id"]]
        print(f"  {c['skill_name']:<20} {s['correct_count']} / {s['total_count']} correct  ->  "
              f"{s['correct_count']} / {s['total_count']} * 100 = {s['score']:g}")

    heading("STEP 3 - Gap table, sorted by priority")
    print(format_gap_report(result["rows"], ROLE))

    heading("STEP 4 - Why is JavaScript a bigger gap than HTML?")
    rows = {r["skill_name"]: r for r in result["rows"]}
    print(" ", explain_gap(rows["JavaScript"]))
    print(" ", explain_gap(rows["HTML"]))
    print("\n ", compare_gaps(result["rows"], "JavaScript", "HTML"))

    heading("STEP 5 - Edge cases the system handles")
    skipped = simulate_submission(role_questions, CORRECT_PER_SKILL, skip_skills=("FE_GIT",))
    r = generate_gap_report(ROLE, skipped, questions, competencies)
    git = next(x for x in r["rows"] if x["skill_id"] == "FE_GIT")
    print(f"  Git questions all skipped  -> current = {git['current']}, gap = {git['gap']}, priority = {git['priority']}")
    print("                                (not treated as 0 or 100; it needs to be assessed)")
    bad = generate_gap_report(ROLE, {"FE_HTML_Q01": "Z"}, questions, competencies)
    print(f"  Invalid answer 'Z'         -> valid = {bad['valid']}, error = {bad['errors'][0]}")

    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    export_gap_report_csv(result["rows"], out_dir / "sample_gap_report_frontend.csv")
    (out_dir / "sample_gap_report_frontend.txt").write_text(format_gap_report(result["rows"], ROLE) + "\n", encoding="utf-8")
    print(f"\n  Saved sample report to {out_dir.name}/sample_gap_report_frontend.txt and .csv")


if __name__ == "__main__":
    main()
