import hashlib
import hmac
import datetime
import os
import re
import secrets
import sqlite3
from pathlib import Path

import extra_streamlit_components as stx
import streamlit as st


DATABASE_PATH = Path("database/classync.db")
_ITERATIONS = 210_000
_SESSION_DAYS = 30
_SESSION_COOKIE = "classync_session"
_cookie_manager = stx.CookieManager(key="classync_auth_cookie")


def _connect():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT 'Classync member',
            username TEXT NOT NULL DEFAULT '',
            bio TEXT NOT NULL DEFAULT '',
            pronouns TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            website TEXT NOT NULL DEFAULT '',
            github TEXT NOT NULL DEFAULT '',
            instagram TEXT NOT NULL DEFAULT '',
            discoverable INTEGER NOT NULL DEFAULT 1,
            banned INTEGER NOT NULL DEFAULT 0,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS login_sessions (
            token_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
        )
        """
    )
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
    if "name" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT 'Classync member'")
    if "username" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN username TEXT NOT NULL DEFAULT ''")
    profile_columns = {
        "bio": "TEXT NOT NULL DEFAULT ''",
        "pronouns": "TEXT NOT NULL DEFAULT ''",
        "location": "TEXT NOT NULL DEFAULT ''",
        "website": "TEXT NOT NULL DEFAULT ''",
        "github": "TEXT NOT NULL DEFAULT ''",
        "instagram": "TEXT NOT NULL DEFAULT ''",
        "discoverable": "INTEGER NOT NULL DEFAULT 1",
        "banned": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, definition in profile_columns.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username) WHERE username != ''"
    )
    connection.execute(
        "UPDATE users SET username = lower(substr(email, 1, instr(email, '@') - 1)) WHERE username = ''"
    )
    connection.commit()
    return connection


def _hash_password(password, salt=None):
    salt_bytes = bytes.fromhex(salt) if salt else secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        _ITERATIONS,
    )
    return password_hash.hex(), salt_bytes.hex()


def register_user(name, username, email, password):
    name = name.strip()
    username = username.strip().lower().lstrip("@")
    email = email.strip().lower()
    if len(name) < 2:
        return False, "Tell us your name so we can personalize your space."
    if not re.fullmatch(r"[a-z0-9_]{3,20}", username):
        return False, "Username must be 3-20 characters using letters, numbers, or underscores."
    if not email or "@" not in email:
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Use at least 8 characters for your password."

    password_hash, salt = _hash_password(password)
    connection = _connect()
    try:
        connection.execute(
            "INSERT INTO users (email, name, username, password_hash, salt) VALUES (?, ?, ?, ?, ?)",
            (email, name, username, password_hash, salt),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        return False, "That email or username is already in use."
    finally:
        connection.close()
    return True, "Account created."


def authenticate_user(email, password):
    email = email.strip().lower()
    connection = _connect()
    try:
        user = connection.execute(
            "SELECT password_hash, salt FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        connection.close()
    if user is None:
        return False

    password_hash, _ = _hash_password(password, user["salt"])
    return hmac.compare_digest(password_hash, user["password_hash"])


def get_user_profile(email):
    connection = _connect()
    try:
        user = connection.execute(
            "SELECT name, username, email, bio, pronouns, location, website, github, instagram, discoverable, banned FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    finally:
        connection.close()
    return dict(user) if user else None


def get_user_profile_by_username(username):
    connection = _connect()
    try:
        user = connection.execute(
            "SELECT name, username, email, bio, pronouns, location, website, github, instagram, discoverable, banned FROM users WHERE username = ?",
            (username.strip().lower().lstrip("@"),),
        ).fetchone()
    finally:
        connection.close()
    return dict(user) if user else None


def search_user_profiles(query, limit=30):
    normalized_query = str(query).strip().lower()
    if not normalized_query:
        return []

    connection = _connect()
    try:
        like_query = f"%{normalized_query}%"
        users = connection.execute(
            """SELECT name, username, bio, pronouns, location, website, github, instagram
               FROM users
               WHERE discoverable = 1 AND banned = 0 AND (lower(name) LIKE ? OR lower(username) LIKE ? OR lower(bio) LIKE ?)
               ORDER BY CASE WHEN lower(username) = ? THEN 0 WHEN lower(username) LIKE ? THEN 1 ELSE 2 END, name COLLATE NOCASE
               LIMIT ?""",
            (like_query, like_query, like_query, normalized_query, f"{normalized_query}%", int(limit)),
        ).fetchall()
    finally:
        connection.close()
    return [dict(user) for user in users]


def update_user_profile(email, name, bio="", pronouns="", location="", website="", github="", instagram="", discoverable=True):
    values = {
        "name": str(name).strip()[:80],
        "bio": str(bio).strip()[:280],
        "pronouns": str(pronouns).strip()[:40],
        "location": str(location).strip()[:80],
        "website": str(website).strip()[:200],
        "github": str(github).strip().lstrip("@").lower()[:39],
        "instagram": str(instagram).strip().lstrip("@").lower()[:30],
        "discoverable": 1 if discoverable else 0,
    }
    if len(values["name"]) < 2:
        return False, "Your display name must be at least 2 characters."

    connection = _connect()
    try:
        connection.execute(
            """UPDATE users
               SET name = ?, bio = ?, pronouns = ?, location = ?, website = ?,
                   github = ?, instagram = ?, discoverable = ?
               WHERE email = ?""",
            (
                values["name"], values["bio"], values["pronouns"], values["location"],
                values["website"], values["github"], values["instagram"],
                values["discoverable"], email.strip().lower(),
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return True, "Profile updated."


def require_auth():
    restore_session()
    if st.session_state.get("authenticated", False) and st.session_state.get("user_banned", False):
        log_out()
    if not st.session_state.get("authenticated", False):
        st.switch_page("pages/login.py")


def _session_token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _create_login_session(email):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=_SESSION_DAYS)
    connection = _connect()
    try:
        connection.execute(
            "INSERT INTO login_sessions (token_hash, email, expires_at) VALUES (?, ?, ?)",
            (_session_token_hash(token), email, expires_at.isoformat()),
        )
        connection.commit()
    finally:
        connection.close()
    return token


def restore_session():
    if st.session_state.get("authenticated", False):
        return True

    token = _cookie_manager.get(_SESSION_COOKIE) or st.query_params.get("session")
    if not token:
        return False

    connection = _connect()
    try:
        session = connection.execute(
            "SELECT email, expires_at FROM login_sessions WHERE token_hash = ?",
            (_session_token_hash(token),),
        ).fetchone()
    finally:
        connection.close()

    if session is None:
        _cookie_manager.delete(_SESSION_COOKIE)
        st.query_params.pop("session", None)
        return False

    expires_at = datetime.datetime.fromisoformat(session["expires_at"])
    if expires_at <= datetime.datetime.now(datetime.timezone.utc):
        connection = _connect()
        try:
            connection.execute(
                "DELETE FROM login_sessions WHERE token_hash = ?",
                (_session_token_hash(token),),
            )
            connection.commit()
        finally:
            connection.close()
        _cookie_manager.delete(_SESSION_COOKIE)
        st.query_params.pop("session", None)
        return False

    log_in(session["email"], create_session=False)
    return True


def log_in(email, name=None, username=None, create_session=True):
    profile = get_user_profile(email)
    if (profile or {}).get("banned", 0):
        return False
    st.session_state.authenticated = True
    st.session_state.user_email = email.strip().lower()
    st.session_state.user_name = name or (profile or {}).get("name", "Classync member")
    st.session_state.user_username = username or (profile or {}).get("username", "member")
    st.session_state.user_banned = bool((profile or {}).get("banned", 0))
    if create_session:
        from backend.admin import log_activity
        log_activity(st.session_state.user_username, "login")
    if create_session:
        token = _create_login_session(st.session_state.user_email)
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=_SESSION_DAYS)
        _cookie_manager.set(
            _SESSION_COOKIE,
            token,
            expires_at=expires_at,
            max_age=_SESSION_DAYS * 24 * 60 * 60,
            same_site="lax",
        )
        st.query_params["session"] = token
    return True


def log_out():
    token = st.query_params.get("session") or _cookie_manager.get(_SESSION_COOKIE)
    if token:
        connection = _connect()
        try:
            connection.execute(
                "DELETE FROM login_sessions WHERE token_hash = ?",
                (_session_token_hash(token),),
            )
            connection.commit()
        finally:
            connection.close()
    st.query_params.pop("session", None)
    _cookie_manager.delete(_SESSION_COOKIE)
    st.session_state.authenticated = False
    st.session_state.pop("user_email", None)
    st.session_state.pop("user_name", None)
    st.session_state.pop("user_username", None)
    st.session_state.pop("user_banned", None)


def get_user_notes_directory():
    username = st.session_state.get("user_username", "member")
    notes_directory = Path("notes") / username
    notes_directory.mkdir(parents=True, exist_ok=True)
    return notes_directory
