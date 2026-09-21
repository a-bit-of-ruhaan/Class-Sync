import datetime
import os
from typing import Any, Dict, List

from backend.auth import _connect
from backend.social import delete_note_image, iter_note_images


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _ensure_tables(connection):
    connection.execute(
        """CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT NOT NULL DEFAULT '',
            details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )"""
    )
    connection.commit()


def admin_emails():
    return {email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()}


def is_admin(email):
    return str(email).strip().lower() in admin_emails()


def log_activity(username, action, target="", details=""):
    connection = _connect()
    try:
        _ensure_tables(connection)
        connection.execute(
            "INSERT INTO activity_log(username, action, target, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, action[:80], target[:160], details[:500], _now()),
        )
        connection.commit()
    finally:
        connection.close()


def list_users() -> List[Dict[str, Any]]:
    connection = _connect()
    try:
        rows = connection.execute(
            "SELECT name, username, email, banned, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def set_user_banned(username, banned, admin_username):
    connection = _connect()
    try:
        cursor = connection.execute(
            "UPDATE users SET banned = ? WHERE username = ?",
            (1 if banned else 0, username),
        )
        connection.commit()
    finally:
        connection.close()
    if cursor.rowcount:
        log_activity(admin_username, "ban_user" if banned else "unban_user", username)
    return cursor.rowcount > 0


def list_activity(limit=100):
    connection = _connect()
    try:
        _ensure_tables(connection)
        rows = connection.execute(
            "SELECT username, action, target, details, created_at FROM activity_log ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def delete_user_note(owner_username, filename, admin_username):
    if delete_note_image(owner_username, filename):
        log_activity(admin_username, "delete_note", f"{owner_username}/{filename}")
        return True
    return False


def user_notes():
    return [(owner, image.name, image) for owner, image in iter_note_images()]
