import datetime
import json

from backend.auth import _connect


def _ensure_table(connection):
    connection.execute(
        """CREATE TABLE IF NOT EXISTS study_plans (
            username TEXT PRIMARY KEY,
            focus TEXT NOT NULL DEFAULT '',
            target_date TEXT NOT NULL,
            tasks_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL
        )"""
    )


def load_study_plan(username):
    connection = _connect()
    try:
        _ensure_table(connection)
        row = connection.execute("SELECT focus, target_date, tasks_json FROM study_plans WHERE username = ?", (username,)).fetchone()
        connection.commit()
    finally:
        connection.close()
    if not row:
        return {"focus": "", "tasks": ["", "", ""], "date": datetime.date.today()}
    try:
        target_date = datetime.date.fromisoformat(row["target_date"])
        tasks = json.loads(row["tasks_json"])
    except (ValueError, TypeError, json.JSONDecodeError):
        target_date = datetime.date.today()
        tasks = ["", "", ""]
    return {"focus": row["focus"], "tasks": (tasks + ["", "", ""])[:3], "date": target_date}


def save_study_plan(username, focus, tasks, target_date):
    clean_tasks = [str(task).strip()[:160] for task in list(tasks)[:3]]
    clean_tasks = (clean_tasks + ["", "", ""])[:3]
    connection = _connect()
    try:
        _ensure_table(connection)
        connection.execute(
            """INSERT INTO study_plans(username, focus, target_date, tasks_json, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(username) DO UPDATE SET focus = excluded.focus,
                 target_date = excluded.target_date, tasks_json = excluded.tasks_json,
                 updated_at = excluded.updated_at""",
            (username, str(focus).strip()[:160], target_date.isoformat(), json.dumps(clean_tasks), datetime.datetime.now(datetime.timezone.utc).isoformat()),
        )
        connection.commit()
    finally:
        connection.close()