"""Member 4 analytics calculations and charts."""
import pandas as pd


def build_gap_table(skill_scores):
    """skill_scores rows: skill_id, skill_name, current_score, target_score."""
    df = pd.DataFrame(skill_scores).copy()
    df["gap"] = (df["target_score"] - df["current_score"]).clip(lower=0)
    df["priority"] = df["gap"].apply(
        lambda gap: "Low" if gap <= 10 else ("Medium" if gap <= 25 else "High")
    )
    df.loc[df["gap"] == 0, "priority"] = "Strong"
    return df


def improvement_summary(assessments: pd.DataFrame):
    if assessments.empty:
        return pd.DataFrame(columns=["skill_id", "date", "score"])
    result = assessments.copy()
    result["score"] = pd.to_numeric(result["score"], errors="coerce")
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    return result.sort_values("date")
