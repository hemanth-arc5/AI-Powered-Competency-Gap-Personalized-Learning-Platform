"""CSV persistence for completed learning tasks and assessment attempts."""
from pathlib import Path
import pandas as pd

TASK_COLUMNS = ["task_id", "student_id", "skill_id", "week", "title", "resource_id", "duration", "status"]
ASSESSMENT_COLUMNS = ["student_id", "attempt_id", "skill_id", "correct_count", "total_count", "score", "date"]


def _ensure_csv(path, columns):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not Path(path).exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)


def save_task(task, path="data/tasks.csv"):
    _ensure_csv(path, TASK_COLUMNS)
    df = pd.read_csv(path)
    new_row = {column: task.get(column, "") for column in TASK_COLUMNS}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(path, index=False)


def update_task_status(task_id, status, path="data/tasks.csv"):
    _ensure_csv(path, TASK_COLUMNS)
    df = pd.read_csv(path)
    if "task_id" not in df.columns or not (df["task_id"].astype(str) == str(task_id)).any():
        return False
    df.loc[df["task_id"].astype(str) == str(task_id), "status"] = status
    df.to_csv(path, index=False)
    return True


def load_tasks(path="data/tasks.csv"):
    _ensure_csv(path, TASK_COLUMNS)
    return pd.read_csv(path)


def save_assessment(result, path="data/assessment_results.csv"):
    _ensure_csv(path, ASSESSMENT_COLUMNS)
    df = pd.read_csv(path)
    new_row = {column: result.get(column, "") for column in ASSESSMENT_COLUMNS}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(path, index=False)


def load_assessments(path="data/assessment_results.csv"):
    _ensure_csv(path, ASSESSMENT_COLUMNS)
    return pd.read_csv(path)
