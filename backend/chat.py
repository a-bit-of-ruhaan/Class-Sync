import datetime
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from backend.auth import _connect
from backend.social import IMAGE_SUFFIXES, iter_note_images


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _ensure_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS chat_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL CHECK(kind IN ('direct', 'group')),
            title TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chat_participants (
            conversation_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            joined_at TEXT NOT NULL,
            last_read_message_id INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (conversation_id, username),
            FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            sender_username TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            shared_note_owner TEXT NOT NULL DEFAULT '',
            shared_note_filename TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS chat_blocks (
            blocker_username TEXT NOT NULL,
            blocked_username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (blocker_username, blocked_username)
        );
        CREATE TABLE IF NOT EXISTS chat_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_username TEXT NOT NULL,
            reported_username TEXT NOT NULL,
            conversation_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chat_presence (
            username TEXT PRIMARY KEY,
            last_seen_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS mate_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_username TEXT NOT NULL,
            receiver_username TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'declined')),
            created_at TEXT NOT NULL,
            responded_at TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS mate_relationships (
            user_a TEXT NOT NULL,
            user_b TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_a, user_b)
        );
        CREATE TABLE IF NOT EXISTS chat_action_log (
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id, id);
        CREATE INDEX IF NOT EXISTS idx_chat_participants_user ON chat_participants(username, conversation_id);
        """
    )


def _open_chat_connection() -> sqlite3.Connection:
    connection = _connect()
    _ensure_tables(connection)
    connection.commit()
    return connection


def _blocked(connection: sqlite3.Connection, first: str, second: str) -> bool:
    return connection.execute(
        """SELECT 1 FROM chat_blocks
           WHERE (blocker_username = ? AND blocked_username = ?)
              OR (blocker_username = ? AND blocked_username = ?)""",
        (first, second, second, first),
    ).fetchone() is not None


def _valid_username(connection: sqlite3.Connection, username: str) -> bool:
    return connection.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone() is not None


def _within_rate_limit(connection, username: str, action: str, limit: int, seconds: int) -> bool:
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds)).isoformat()
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM chat_action_log WHERE username = ? AND action = ? AND created_at >= ?",
        (username, action, cutoff),
    ).fetchone()["count"]
    if count >= limit:
        return False
    connection.execute("INSERT INTO chat_action_log(username, action, created_at) VALUES (?, ?, ?)", (username, action, _now()))
    return True


def _mate_pair(first: str, second: str) -> tuple[str, str]:
    return tuple(sorted((first, second)))


def _are_mates_connection(connection: sqlite3.Connection, first: str, second: str) -> bool:
    user_a, user_b = _mate_pair(first, second)
    return connection.execute(
        "SELECT 1 FROM mate_relationships WHERE user_a = ? AND user_b = ?",
        (user_a, user_b),
    ).fetchone() is not None


def are_mates(first: str, second: str) -> bool:
    if first == second:
        return False
    connection = _open_chat_connection()
    try:
        return _are_mates_connection(connection, first, second)
    finally:
        connection.close()


def get_mate_status(viewer_username: str, other_username: str) -> Dict[str, Any]:
    if viewer_username == other_username:
        return {"status": "self", "request_id": None}
    connection = _open_chat_connection()
    try:
        if _are_mates_connection(connection, viewer_username, other_username):
            return {"status": "mates", "request_id": None}
        request = connection.execute(
            """SELECT id, sender_username, receiver_username FROM mate_requests
               WHERE status = 'pending' AND ((sender_username = ? AND receiver_username = ?)
                  OR (sender_username = ? AND receiver_username = ?))
               ORDER BY id DESC LIMIT 1""",
            (viewer_username, other_username, other_username, viewer_username),
        ).fetchone()
        if not request:
            return {"status": "none", "request_id": None}
        status = "sent" if request["sender_username"] == viewer_username else "received"
        return {"status": status, "request_id": request["id"]}
    finally:
        connection.close()


def send_mate_request(sender_username: str, receiver_username: str) -> bool:
    if sender_username == receiver_username:
        return False
    connection = _open_chat_connection()
    try:
        if not _within_rate_limit(connection, sender_username, "mate_request", 20, 3600):
            return False
        if not _valid_username(connection, receiver_username) or _blocked(connection, sender_username, receiver_username):
            return False
        if _are_mates_connection(connection, sender_username, receiver_username):
            return False
        pending_request = connection.execute(
            """SELECT 1 FROM mate_requests WHERE status = 'pending'
               AND ((sender_username = ? AND receiver_username = ?)
                 OR (sender_username = ? AND receiver_username = ?))""",
            (sender_username, receiver_username, receiver_username, sender_username),
        ).fetchone()
        if pending_request:
            return False
        connection.execute(
            "INSERT INTO mate_requests(sender_username, receiver_username, created_at) VALUES (?, ?, ?)",
            (sender_username, receiver_username, _now()),
        )
        connection.commit()
        return True
    finally:
        connection.close()


def respond_to_mate_request(request_id: int, receiver_username: str, accept: bool) -> bool:
    connection = _open_chat_connection()
    try:
        request = connection.execute(
            "SELECT sender_username, receiver_username FROM mate_requests WHERE id = ? AND status = 'pending'",
            (request_id,),
        ).fetchone()
        if not request or request["receiver_username"] != receiver_username:
            return False
        now = _now()
        connection.execute(
            "UPDATE mate_requests SET status = ?, responded_at = ? WHERE id = ?",
            ("accepted" if accept else "declined", now, request_id),
        )
        if accept:
            user_a, user_b = _mate_pair(request["sender_username"], request["receiver_username"])
            connection.execute(
                "INSERT OR IGNORE INTO mate_relationships(user_a, user_b, created_at) VALUES (?, ?, ?)",
                (user_a, user_b, now),
            )
        connection.commit()
        return True
    finally:
        connection.close()


def list_mate_requests(username: str) -> List[Dict[str, Any]]:
    connection = _open_chat_connection()
    try:
        rows = connection.execute(
            """SELECT r.id, r.sender_username, u.name, r.created_at
               FROM mate_requests r JOIN users u ON u.username = r.sender_username
               WHERE r.receiver_username = ? AND r.status = 'pending' ORDER BY r.id DESC""",
            (username,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def list_mates(username: str) -> List[Dict[str, Any]]:
    connection = _open_chat_connection()
    try:
        rows = connection.execute(
            """SELECT u.name, u.username, u.bio
               FROM mate_relationships r JOIN users u
                 ON u.username = CASE WHEN r.user_a = ? THEN r.user_b ELSE r.user_a END
               WHERE r.user_a = ? OR r.user_b = ? ORDER BY u.name COLLATE NOCASE""",
            (username, username, username),
        ).fetchall()
        return [
            {"name": row["name"], "username": row["username"], "bio": row["bio"], "online": is_user_online(row["username"])}
            for row in rows
        ]
    finally:
        connection.close()


def remove_mate(username: str, other_username: str) -> bool:
    user_a, user_b = _mate_pair(username, other_username)
    connection = _open_chat_connection()
    try:
        cursor = connection.execute("DELETE FROM mate_relationships WHERE user_a = ? AND user_b = ?", (user_a, user_b))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def touch_presence(username: str) -> None:
    connection = _open_chat_connection()
    try:
        connection.execute(
            "INSERT INTO chat_presence(username, last_seen_at) VALUES (?, ?) ON CONFLICT(username) DO UPDATE SET last_seen_at = excluded.last_seen_at",
            (username, _now()),
        )
        connection.commit()
    finally:
        connection.close()


def is_user_online(username: str, within_seconds: int = 300) -> bool:
    connection = _open_chat_connection()
    try:
        presence = connection.execute("SELECT last_seen_at FROM chat_presence WHERE username = ?", (username,)).fetchone()
    finally:
        connection.close()
    if not presence:
        return False
    last_seen = datetime.datetime.fromisoformat(presence["last_seen_at"])
    return (datetime.datetime.now(datetime.timezone.utc) - last_seen).total_seconds() <= within_seconds


def list_chat_users(username: str) -> List[Dict[str, Any]]:
    connection = _open_chat_connection()
    try:
        users = connection.execute(
            "SELECT name, username, bio FROM users WHERE username != ? AND discoverable = 1 AND banned = 0 ORDER BY name COLLATE NOCASE",
            (username,),
        ).fetchall()
        return [
            {"name": row["name"], "username": row["username"], "bio": row["bio"], "online": is_user_online(row["username"])}
            for row in users
            if not _blocked(connection, username, row["username"])
        ]
    finally:
        connection.close()


def create_direct_conversation(username: str, other_username: str) -> int | None:
    if username == other_username:
        return None
    connection = _open_chat_connection()
    try:
        if not _valid_username(connection, other_username) or _blocked(connection, username, other_username) or not _are_mates_connection(connection, username, other_username):
            return None
        existing = connection.execute(
            """SELECT c.id FROM chat_conversations c
               JOIN chat_participants p ON p.conversation_id = c.id
               WHERE c.kind = 'direct' AND p.username IN (?, ?)
               GROUP BY c.id HAVING COUNT(DISTINCT p.username) = 2""",
            (username, other_username),
        ).fetchone()
        if existing:
            return int(existing["id"])
        now = _now()
        cursor = connection.execute(
            "INSERT INTO chat_conversations(kind, created_by, created_at, updated_at) VALUES ('direct', ?, ?, ?)",
            (username, now, now),
        )
        conversation_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO chat_participants(conversation_id, username, joined_at) VALUES (?, ?, ?)",
            [(conversation_id, username, now), (conversation_id, other_username, now)],
        )
        connection.commit()
        return int(conversation_id)
    finally:
        connection.close()


def create_group_conversation(username: str, title: str, members: List[str]) -> int | None:
    clean_members = sorted(set(member.strip().lower().lstrip("@") for member in members if member.strip()))
    clean_members = [member for member in clean_members if member != username]
    if not clean_members or len(clean_members) > 24 or not title.strip():
        return None
    connection = _open_chat_connection()
    try:
        if any(not _valid_username(connection, member) or _blocked(connection, username, member) for member in clean_members):
            return None
        now = _now()
        cursor = connection.execute(
            "INSERT INTO chat_conversations(kind, title, created_by, created_at, updated_at) VALUES ('group', ?, ?, ?, ?)",
            (title.strip()[:80], username, now, now),
        )
        conversation_id = cursor.lastrowid
        participants = [username] + clean_members
        connection.executemany(
            "INSERT INTO chat_participants(conversation_id, username, joined_at) VALUES (?, ?, ?)",
            [(conversation_id, member, now) for member in participants],
        )
        connection.commit()
        return int(conversation_id)
    finally:
        connection.close()


def list_conversations(username: str) -> List[Dict[str, Any]]:
    connection = _open_chat_connection()
    try:
        rows = connection.execute(
            """SELECT c.id, c.kind, c.title, c.updated_at, p.last_read_message_id
               FROM chat_conversations c JOIN chat_participants p ON p.conversation_id = c.id
               WHERE p.username = ? ORDER BY c.updated_at DESC""",
            (username,),
        ).fetchall()
        conversations = []
        for row in rows:
            participants = connection.execute(
                """SELECT p.username, u.name FROM chat_participants p
                   LEFT JOIN users u ON u.username = p.username
                   WHERE p.conversation_id = ? ORDER BY u.name COLLATE NOCASE""",
                (row["id"],),
            ).fetchall()
            messages = connection.execute(
                "SELECT id, sender_username, body, shared_note_filename, created_at FROM chat_messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 1",
                (row["id"],),
            ).fetchone()
            unread = connection.execute(
                "SELECT COUNT(*) AS count FROM chat_messages WHERE conversation_id = ? AND id > ? AND sender_username != ?",
                (row["id"], row["last_read_message_id"], username),
            ).fetchone()["count"]
            conversations.append({
                "id": row["id"], "kind": row["kind"], "title": row["title"],
                "participants": [dict(participant) for participant in participants],
                "last_message": dict(messages) if messages else None, "unread": int(unread),
            })
        return conversations
    finally:
        connection.close()


def get_unread_count(username: str) -> int:
    return sum(conversation["unread"] for conversation in list_conversations(username))


def get_messages(conversation_id: int, username: str) -> List[Dict[str, Any]]:
    connection = _open_chat_connection()
    try:
        if connection.execute("SELECT 1 FROM chat_participants WHERE conversation_id = ? AND username = ?", (conversation_id, username)).fetchone() is None:
            return []
        rows = connection.execute(
            """SELECT id, sender_username, body, shared_note_owner, shared_note_filename, created_at
               FROM chat_messages WHERE conversation_id = ? ORDER BY id""",
            (conversation_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def mark_conversation_read(conversation_id: int, username: str) -> None:
    connection = _open_chat_connection()
    try:
        latest = connection.execute("SELECT COALESCE(MAX(id), 0) AS id FROM chat_messages WHERE conversation_id = ?", (conversation_id,)).fetchone()["id"]
        connection.execute("UPDATE chat_participants SET last_read_message_id = ? WHERE conversation_id = ? AND username = ?", (latest, conversation_id, username))
        connection.commit()
    finally:
        connection.close()


def send_message(conversation_id: int, username: str, body: str = "", note_owner: str = "", note_filename: str = "") -> bool:
    body = body.strip()[:2000]
    connection = _open_chat_connection()
    try:
        participant = connection.execute("SELECT 1 FROM chat_participants WHERE conversation_id = ? AND username = ?", (conversation_id, username)).fetchone()
        if participant is None or (not body and not note_filename):
            return False
        if not _within_rate_limit(connection, username, "message", 60, 60):
            return False
        conversation = connection.execute("SELECT kind FROM chat_conversations WHERE id = ?", (conversation_id,)).fetchone()
        if conversation and conversation["kind"] == "direct":
            other = connection.execute(
                "SELECT username FROM chat_participants WHERE conversation_id = ? AND username != ? LIMIT 1",
                (conversation_id, username),
            ).fetchone()
            if not other or not _are_mates_connection(connection, username, other["username"]):
                return False
        if note_filename:
            note_path = Path("notes") / note_owner / Path(note_filename).name
            if note_owner != username or Path(note_filename).name != note_filename or not note_path.is_file() or note_path.suffix.lower() not in IMAGE_SUFFIXES:
                return False
        now = _now()
        connection.execute(
            "INSERT INTO chat_messages(conversation_id, sender_username, body, shared_note_owner, shared_note_filename, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, username, body, note_owner, note_filename, now),
        )
        connection.execute("UPDATE chat_conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        connection.commit()
        from backend.admin import log_activity
        log_activity(username, "send_message", str(conversation_id), "note shared" if note_filename else "message sent")
        return True
    finally:
        connection.close()


def block_user(username: str, blocked_username: str) -> bool:
    if username == blocked_username:
        return False
    connection = _open_chat_connection()
    try:
        connection.execute("INSERT OR IGNORE INTO chat_blocks VALUES (?, ?, ?)", (username, blocked_username, _now()))
        connection.commit()
        return True
    finally:
        connection.close()


def report_user(reporter: str, reported: str, conversation_id: int, reason: str) -> bool:
    if not reason.strip():
        return False
    connection = _open_chat_connection()
    try:
        connection.execute(
            "INSERT INTO chat_reports(reporter_username, reported_username, conversation_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
            (reporter, reported, conversation_id, reason.strip()[:500], _now()),
        )
        connection.commit()
        return True
    finally:
        connection.close()


def list_shareable_notes(username: str) -> List[Path]:
    return [path for owner, path in iter_note_images() if owner == username]