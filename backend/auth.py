import hashlib
import hmac
import datetime
import re
import secrets
import sqlite3
from pathlib import Path

import streamlit as st


DATABASE_PATH = Path("database/classync.db")
_ITERATIONS = 210_000
_SESSION_DAYS = 30


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
            "SELECT name, username, email FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    finally:
        connection.close()
    return dict(user) if user else None


def get_user_profile_by_username(username):
    connection = _connect()
    try:
        user = connection.execute(
            "SELECT name, username, email FROM users WHERE username = ?",
            (username.strip().lower().lstrip("@"),),
        ).fetchone()
    finally:
        connection.close()
    return dict(user) if user else None


def require_auth():
    restore_session()
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

    token = st.query_params.get("session")
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
        st.query_params.pop("session", None)
        return False

    log_in(session["email"], create_session=False)
    return True


def log_in(email, name=None, username=None, create_session=True):
    profile = get_user_profile(email)
    st.session_state.authenticated = True
    st.session_state.user_email = email.strip().lower()
    st.session_state.user_name = name or (profile or {}).get("name", "Classync member")
    st.session_state.user_username = username or (profile or {}).get("username", "member")
    if create_session:
        st.query_params["session"] = _create_login_session(st.session_state.user_email)


def log_out():
    token = st.query_params.get("session")
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
    st.session_state.authenticated = False
    st.session_state.pop("user_email", None)
    st.session_state.pop("user_name", None)
    st.session_state.pop("user_username", None)


def get_user_notes_directory():
    username = st.session_state.get("user_username", "member")
    notes_directory = Path("notes") / username
    notes_directory.mkdir(parents=True, exist_ok=True)
    return notes_directory
