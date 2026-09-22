import datetime
import json
from pathlib import Path

from backend.auth import _connect


NOTE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf", ".txt", ".doc", ".docx", ".md", ".csv", ".json"}
INTERNAL_FILENAMES = {".social.json", ".uploaders.json", "social.json"}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _ensure_tables(connection):
    connection.execute(
        """CREATE TABLE IF NOT EXISTS note_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_username TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'General',
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS note_request_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            responder_username TEXT NOT NULL,
            filename TEXT NOT NULL,
            message TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES note_requests(id) ON DELETE CASCADE
        )"""
    )
    connection.commit()


def create_request(requester_username, title, description, category):
    title = str(title).strip()[:120]
    description = str(description).strip()[:500]
    category = str(category).strip()[:50] or "General"
    if not title:
        return None

    connection = _connect()
    try:
        _ensure_tables(connection)
        cursor = connection.execute(
            "INSERT INTO note_requests(requester_username, title, description, category, created_at) VALUES (?, ?, ?, ?, ?)",
            (requester_username, title, description, category, _now()),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def list_requests(status="open"):
    connection = _connect()
    try:
        _ensure_tables(connection)
        if status == "all":
            rows = connection.execute(
                "SELECT id, requester_username, title, description, category, status, created_at FROM note_requests ORDER BY id DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT id, requester_username, title, description, category, status, created_at FROM note_requests WHERE status = ? ORDER BY id DESC",
                (status,),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def list_responses(request_id):
    connection = _connect()
    try:
        _ensure_tables(connection)
        rows = connection.execute(
            "SELECT id, request_id, responder_username, filename, message, created_at FROM note_request_responses WHERE request_id = ? ORDER BY id DESC",
            (int(request_id),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def list_user_note_files(username):
    notes_dir = Path("notes") / username
    if not notes_dir.exists():
        return []
    return sorted(
        [
            item
            for item in notes_dir.iterdir()
            if item.is_file()
            and item.name.lower() not in INTERNAL_FILENAMES
            and item.suffix.lower() in NOTE_SUFFIXES
        ],
        key=lambda item: item.name.casefold(),
    )


def save_uploaded_photo(username, uploaded_file):
    original_name = Path(getattr(uploaded_file, "name", "photo.jpg")).name
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
        return None

    file_size = int(getattr(uploaded_file, "size", 0) or 0)
    if file_size > 50 * 1024 * 1024:
        return None

    notes_dir = Path("notes") / username
    notes_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(original_name).stem.strip()[:60] or "shared-photo"
    candidate = notes_dir / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = notes_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    candidate.write_bytes(uploaded_file.getbuffer())
    return candidate


def create_response(request_id, responder_username, filename, message=""):
    return create_responses(request_id, responder_username, [filename], message)


def create_responses(request_id, responder_username, filenames, message=""):
    safe_filenames = []
    for filename in filenames:
        safe_filename = Path(filename).name
        if safe_filename != filename or safe_filename.lower() in INTERNAL_FILENAMES or Path(safe_filename).suffix.lower() not in NOTE_SUFFIXES:
            return False

        note_path = Path("notes") / responder_username / safe_filename
        if not note_path.is_file():
            return False
        safe_filenames.append(safe_filename)

    if not safe_filenames:
        return False

    connection = _connect()
    try:
        _ensure_tables(connection)
        request = connection.execute("SELECT id, status FROM note_requests WHERE id = ?", (int(request_id),)).fetchone()
        if request is None or request["status"] != "open":
            return False
        created_at = _now()
        connection.executemany(
            "INSERT INTO note_request_responses(request_id, responder_username, filename, message, created_at) VALUES (?, ?, ?, ?, ?)",
            [(int(request_id), responder_username, filename, str(message).strip()[:300], created_at) for filename in safe_filenames],
        )
        connection.execute("UPDATE note_requests SET status = 'fulfilled' WHERE id = ?", (int(request_id),))
        connection.commit()
        return True
    finally:
        connection.close()


def response_file(response):
    safe_filename = Path(response["filename"]).name
    if safe_filename != response["filename"]:
        return None
    note_path = Path("notes") / response["responder_username"] / safe_filename
    return note_path if note_path.is_file() else None
