import datetime
import json
import re
from typing import Any, Dict, Iterable, List

from backend.auth import _connect


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _ensure_tables(connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS quiz_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_by TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            completed_at TEXT NOT NULL,
            FOREIGN KEY (game_id) REFERENCES quiz_games(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_game ON quiz_attempts(game_id, score DESC, total DESC);
        """
    )


def _open_connection():
    connection = _connect()
    _ensure_tables(connection)
    connection.commit()
    return connection


def parse_quiz_response(response: str, question_limit: int = 10) -> Dict[str, Any]:
    cleaned = str(response).strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("The AI response did not contain a JSON quiz.")
    try:
        payload = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as error:
        raise ValueError("The AI response contained invalid quiz JSON.") from error

    questions = payload.get("questions") if isinstance(payload, dict) else None
    if not isinstance(questions, list) or not 2 <= len(questions) <= question_limit:
        raise ValueError("The generated quiz did not contain enough valid questions.")

    normalized_questions = []
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("A generated quiz question was malformed.")
        prompt = str(question.get("question", "")).strip()
        options = [str(option).strip() for option in question.get("options", []) if str(option).strip()][:4]
        answer = question.get("answer")
        explanation = str(question.get("explanation", "")).strip()
        if not prompt or len(options) < 2 or not isinstance(answer, int) or not 0 <= answer < len(options):
            raise ValueError("A generated quiz question had invalid options or answer data.")
        normalized_questions.append({
            "question": prompt[:500],
            "options": options,
            "answer": answer,
            "explanation": explanation[:500],
        })
    return {"questions": normalized_questions}


def create_quiz(title: str, questions: List[Dict[str, Any]], username: str) -> int:
    connection = _open_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO quiz_games(title, created_by, questions_json, created_at) VALUES (?, ?, ?, ?)",
            (title.strip()[:100] or "Study quiz", username, json.dumps({"questions": questions}), _now()),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def list_quizzes(limit: int = 30) -> List[Dict[str, Any]]:
    connection = _open_connection()
    try:
        rows = connection.execute(
            "SELECT id, title, created_by, created_at, questions_json FROM quiz_games ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [
            {"id": row["id"], "title": row["title"], "created_by": row["created_by"], "created_at": row["created_at"], "questions": json.loads(row["questions_json"])["questions"]}
            for row in rows
        ]
    finally:
        connection.close()


def record_attempt(game_id: int, username: str, score: int, total: int) -> bool:
    if total <= 0 or score < 0 or score > total:
        return False
    connection = _open_connection()
    try:
        exists = connection.execute("SELECT 1 FROM quiz_games WHERE id = ?", (game_id,)).fetchone()
        if not exists:
            return False
        connection.execute(
            "INSERT INTO quiz_attempts(game_id, username, score, total, completed_at) VALUES (?, ?, ?, ?, ?)",
            (game_id, username, score, total, _now()),
        )
        connection.commit()
        return True
    finally:
        connection.close()


def get_leaderboard(game_id: int, usernames: Iterable[str] | None = None) -> List[Dict[str, Any]]:
    connection = _open_connection()
    try:
        params: List[Any] = [game_id]
        filter_sql = ""
        allowed = list(dict.fromkeys(usernames or []))
        if usernames is not None:
            if not allowed:
                return []
            placeholders = ", ".join("?" for _ in allowed)
            filter_sql = f" AND a.username IN ({placeholders})"
            params.extend(allowed)
        rows = connection.execute(
            f"""WITH ranked_attempts AS (
                   SELECT a.username, a.score, a.total, a.completed_at,
                          CAST(a.score AS REAL) / a.total AS percentage,
                          ROW_NUMBER() OVER (
                              PARTITION BY a.username
                              ORDER BY CAST(a.score AS REAL) / a.total DESC,
                                       a.score DESC, a.total DESC, a.completed_at ASC
                          ) AS rank_number
                   FROM quiz_attempts a
                   WHERE a.game_id = ?{filter_sql}
               )
             SELECT ranked_attempts.username, u.name, ranked_attempts.percentage,
                      ranked_attempts.score, ranked_attempts.total, ranked_attempts.completed_at
               FROM ranked_attempts JOIN users u ON u.username = ranked_attempts.username AND u.banned = 0
               WHERE ranked_attempts.rank_number = 1
               ORDER BY ranked_attempts.percentage DESC, ranked_attempts.score DESC,
                        ranked_attempts.completed_at ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()