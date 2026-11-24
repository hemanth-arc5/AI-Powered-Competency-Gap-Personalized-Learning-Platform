"""Member 4: curated learning resources and priority-based recommendations."""
from __future__ import annotations
import pandas as pd

RESOURCE_COLUMNS = ["resource_id", "skill_id", "title", "url", "level", "type", "duration"]
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Strong": 3}


def load_resources(path: str = "data/resources.csv") -> pd.DataFrame:
    """Load and validate the curated resource catalogue."""
    df = pd.read_csv(path)
    missing = [column for column in RESOURCE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Resource catalogue is missing columns: {missing}")
    return df[RESOURCE_COLUMNS].fillna("")


def recommend_resources(gaps, resources: pd.DataFrame, prerequisites=None) -> pd.DataFrame:
    """Return resources for gaps, with High before Medium before Low.

    gaps may be a DataFrame or a list of dictionaries containing skill_id,
    skill_name, gap and priority. prerequisites maps a skill_id to prerequisite
    skill IDs, for example {"javascript": ["html", "css"]}.
    """
    if isinstance(gaps, pd.DataFrame):
        gap_rows = gaps.to_dict(orient="records")
    else:
        gap_rows = list(gaps)
    prerequisites = prerequisites or {}
    priority_rank = {"High": 0, "Medium": 1, "Low": 2, "Strong": 3}

    # Prerequisites are used as an ordering hint: a prerequisite is placed
    # before the skill that depends on it when both appear in the gap list.
    skills = {str(row.get("skill_id", row.get("skill_name", ""))).lower(): row for row in gap_rows}
    prereq_depth = {}
    def depth(skill, seen=None):
        seen = set() if seen is None else seen
        if skill in seen:
            return 0
        seen.add(skill)
        parents = prerequisites.get(skill, [])
        return 0 if not parents else 1 + max(depth(p, seen.copy()) for p in parents)
    for skill in skills:
        prereq_depth[skill] = depth(skill)

    gap_rows.sort(key=lambda r: (
        priority_rank.get(str(r.get("priority", "Low")), 2),
        -float(r.get("gap", 0) or 0),
        prereq_depth.get(str(r.get("skill_id", r.get("skill_name", ""))).lower(), 0),
    ))

    results = []
    for gap in gap_rows:
        skill_id = str(gap.get("skill_id", gap.get("skill_name", "")))
        priority = str(gap.get("priority", "Low"))
        if priority in ("Strong", "None") or float(gap.get("gap", 0) or 0) <= 0:
            continue
        matches = resources[resources["skill_id"].astype(str).str.lower() == skill_id.lower()].copy()
        if matches.empty:
            results.append({
                "skill_id": skill_id,
                "skill_name": gap.get("skill_name", skill_id),
                "priority": priority,
                "gap": gap.get("gap", 0),
                "title": "No curated resource available",
                "url": "",
                "level": "",
                "type": "",
                "duration": "",
            })
        else:
            for item in matches.to_dict(orient="records"):
                results.append({
                    "skill_id": skill_id,
                    "skill_name": gap.get("skill_name", skill_id),
                    "priority": priority,
                    "gap": gap.get("gap", 0),
                    **{k: item.get(k, "") for k in ["title", "url", "level", "type", "duration"]},
                })
    return pd.DataFrame(results)
