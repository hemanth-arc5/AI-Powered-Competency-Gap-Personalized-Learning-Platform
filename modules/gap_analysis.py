"""Gap-analysis module (Member 2).

Core formula (all values are on a 0-100 scale):

    gap = max(0, target - current)

Priority labels (project-defined thresholds, not universal standards):

    gap = 0        -> Strong        (target met or exceeded)
    1  to 10       -> Low
    11 to 25       -> Medium
    above 25       -> High
    no score       -> Not Assessed  (we do not know, so we do not guess)

The AI layer (Member 3) must only EXPLAIN these numbers; it never calculates them.
"""
import csv

from modules.scoring import (
    calculate_skill_scores,
    get_questions_for_skills,
    get_role_competencies,
    validate_submission,
)

LOW_MAX = 10      # gap <= 10  -> Low
MEDIUM_MAX = 25   # gap <= 25  -> Medium, above -> High

PRIORITY_STRONG = "Strong"
PRIORITY_LOW = "Low"
PRIORITY_MEDIUM = "Medium"
PRIORITY_HIGH = "High"
PRIORITY_NOT_ASSESSED = "Not Assessed"

# A weak prerequisite (Medium/High gap) should be learned before the skill that needs it.
BLOCKING_PRIORITIES = (PRIORITY_MEDIUM, PRIORITY_HIGH)


# --------------------------------------------------------------------------- #
# The two formulas
# --------------------------------------------------------------------------- #
def calculate_gap(target, current):
    """gap = max(0, target - current).  Returns None when current is None (not assessed)."""
    if not 0 <= target <= 100:
        raise ValueError(f"target must be between 0 and 100, got {target}")
    if current is None:
        return None
    if not 0 <= current <= 100:
        raise ValueError(f"current score must be between 0 and 100, got {current}")
    return round(max(0, target - current), 2)


def priority_label(gap):
    """Convert a gap into Strong / Low / Medium / High (or Not Assessed for None)."""
    if gap is None:
        return PRIORITY_NOT_ASSESSED
    if gap < 0:
        raise ValueError("gap cannot be negative; use calculate_gap()")
    if gap == 0:
        return PRIORITY_STRONG
    if gap <= LOW_MAX:
        return PRIORITY_LOW
    if gap <= MEDIUM_MAX:
        return PRIORITY_MEDIUM
    return PRIORITY_HIGH


def _num(value):
    """Format 80.0 as '80' and 33.33 as '33.33' for readable formulas."""
    return f"{value:g}"


def formula_text(target, current, gap):
    """The formula with the real numbers filled in (used in the report and in the viva)."""
    if gap is None:
        return "not assessed (no score, so no gap is calculated)"
    return f"max(0, {_num(target)} - {_num(current)}) = {_num(gap)}"


# --------------------------------------------------------------------------- #
# Building, sorting and summarising the gap table
# --------------------------------------------------------------------------- #
def build_gap_rows(skill_scores, role_competencies):
    """One row per competency of the role (unsorted).

    Row keys: skill_id, skill_name, role, current, target, gap, priority, status,
              prerequisites, learn_first, formula
    learn_first = prerequisites that themselves have a Medium/High gap.
    """
    rows = {}
    for comp in role_competencies:
        score_info = skill_scores.get(comp["skill_id"])
        current = score_info["score"] if score_info else None
        status = score_info["status"] if score_info else "no_questions"
        gap = calculate_gap(comp["target_score"], current)
        rows[comp["skill_id"]] = {
            "skill_id": comp["skill_id"],
            "skill_name": comp["skill_name"],
            "role": comp["role"],
            "current": current,
            "target": comp["target_score"],
            "gap": gap,
            "priority": priority_label(gap),
            "status": status,
            "prerequisites": list(comp["prerequisites"]),
            "learn_first": [],
            "formula": formula_text(comp["target_score"], current, gap),
        }
    for row in rows.values():
        row["learn_first"] = [p for p in row["prerequisites"]
                              if p in rows and rows[p]["priority"] in BLOCKING_PRIORITIES]
    return list(rows.values())


def sort_gaps(rows):
    """Biggest gap first.  Ties: higher target first, then name (so the order is deterministic).
    Skills that were not assessed go to the bottom, alphabetically."""
    assessed = [r for r in rows if r["gap"] is not None]
    not_assessed = [r for r in rows if r["gap"] is None]
    assessed.sort(key=lambda r: (-r["gap"], -r["target"], r["skill_name"]))
    not_assessed.sort(key=lambda r: r["skill_name"])
    return assessed + not_assessed


def summarize_gaps(rows):
    """Counts per priority plus the biggest gap and the list of skills that were not assessed."""
    counts = {p: 0 for p in (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
                             PRIORITY_STRONG, PRIORITY_NOT_ASSESSED)}
    for r in rows:
        counts[r["priority"]] += 1
    ordered = sort_gaps(rows)
    biggest = ordered[0] if ordered and ordered[0]["gap"] else None
    return {
        "total_skills": len(rows),
        "counts": counts,
        "biggest_gap": biggest["skill_name"] if biggest else None,
        "not_assessed": [r["skill_name"] for r in rows if r["gap"] is None],
    }


# --------------------------------------------------------------------------- #
# Explaining (for the viva and for the UI)
# --------------------------------------------------------------------------- #
def explain_gap(row):
    """One-line explanation of a single skill."""
    if row["gap"] is None:
        return f"{row['skill_name']}: not assessed, so no gap can be calculated."
    return (f"{row['skill_name']}: current {_num(row['current'])}, target {_num(row['target'])} "
            f"-> gap = {row['formula']} -> {row['priority']}")


def compare_gaps(rows, skill_a, skill_b):
    """Explain which of two skills (by skill_name or skill_id) is the bigger gap, with the numbers."""
    def find(key):
        for r in rows:
            if key.lower() in (r["skill_name"].lower(), r["skill_id"].lower()):
                return r
        raise ValueError(f"Skill '{key}' not found in the gap table.")

    a, b = find(skill_a), find(skill_b)
    for r in (a, b):
        if r["gap"] is None:
            return f"Cannot compare: {r['skill_name']} was not assessed."
    detail = (f"{a['skill_name']}: {a['formula']} ({a['priority']}); "
              f"{b['skill_name']}: {b['formula']} ({b['priority']}).")
    if a["gap"] > b["gap"]:
        return f"{a['skill_name']} is a bigger gap than {b['skill_name']}. {detail}"
    if b["gap"] > a["gap"]:
        return f"{b['skill_name']} is a bigger gap than {a['skill_name']}. {detail}"
    return f"{a['skill_name']} and {b['skill_name']} have the same gap. {detail}"


def format_gap_report(rows, role=None):
    """Plain-text table, already sorted by priority (call sort_gaps first)."""
    lines = []
    if role:
        lines.append(f"GAP ANALYSIS REPORT - {role}")
    lines.append("Formula: gap = max(0, target - current)   |   High > 25, Medium 11-25, Low 1-10, Strong = 0")
    header = f"{'#':>2}  {'Skill':<20}{'Current':>8}{'Target':>8}{'Gap':>6}  {'Priority':<13}Calculation"
    lines += ["", header, "-" * len(header) + "-" * 20]
    for rank, r in enumerate(rows, start=1):
        current = "-" if r["current"] is None else _num(r["current"])
        gap = "-" if r["gap"] is None else _num(r["gap"])
        lines.append(f"{rank:>2}  {r['skill_name']:<20}{current:>8}{_num(r['target']):>8}{gap:>6}  "
                     f"{r['priority']:<13}{r['formula']}")
    learn_first = [r for r in rows if r["learn_first"]]
    if learn_first:
        lines.append("")
        for r in learn_first:
            names = ", ".join(next(x["skill_name"] for x in rows if x["skill_id"] == p) for p in r["learn_first"])
            lines.append(f"Note: strengthen {names} before {r['skill_name']} (prerequisite has a Medium/High gap).")
    return "\n".join(lines)


def export_gap_report_csv(rows, path):
    """Save the sorted gap table as CSV (for the dashboard / test evidence)."""
    fields = ["rank", "skill_id", "skill_name", "current", "target", "gap", "priority", "status", "learn_first", "formula"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rank, r in enumerate(rows, start=1):
            writer.writerow({
                "rank": rank, "skill_id": r["skill_id"], "skill_name": r["skill_name"],
                "current": "" if r["current"] is None else r["current"],
                "target": r["target"],
                "gap": "" if r["gap"] is None else r["gap"],
                "priority": r["priority"], "status": r["status"],
                "learn_first": "|".join(r["learn_first"]), "formula": r["formula"],
            })


# --------------------------------------------------------------------------- #
# One call for the whole pipeline (Member 1 / Member 3 / Member 4 call this)
# --------------------------------------------------------------------------- #
def generate_gap_report(role, submission, questions, competencies):
    """Validate -> score -> gap -> priority -> sort.

    Returns a dict:
      valid, errors, warnings   - validation outcome (rows are empty when valid is False)
      skill_scores              - {skill_id: per-skill score info}
      rows                      - gap rows sorted by priority (see build_gap_rows)
      summary                   - counts per priority, biggest gap, skills not assessed
    """
    role_competencies = get_role_competencies(competencies, role)
    skill_ids = [c["skill_id"] for c in role_competencies]
    role_questions = get_questions_for_skills(questions, skill_ids)

    validation = validate_submission(submission, role_questions)
    if not validation.valid:
        return {"valid": False, "errors": validation.errors, "warnings": validation.warnings,
                "skill_scores": {}, "rows": [], "summary": None}

    skill_scores = calculate_skill_scores(role_questions, submission, skill_ids)
    rows = sort_gaps(build_gap_rows(skill_scores, role_competencies))
    return {"valid": True, "errors": [], "warnings": validation.warnings,
            "skill_scores": skill_scores, "rows": rows, "summary": summarize_gaps(rows)}
