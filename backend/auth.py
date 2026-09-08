import hashlib
import hmac
import re
import secrets
import sqlite3
from pathlib import Path

import streamlit as st


DATABASE_PATH = Path("database/classync.db")
_ITERATIONS = 210_000


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


def require_auth():
    if not st.session_state.get("authenticated", False):
        st.switch_page("pages/login.py")


def log_in(email, name=None, username=None):
    profile = get_user_profile(email)
    st.session_state.authenticated = True
    st.session_state.user_email = email.strip().lower()
    st.session_state.user_name = name or (profile or {}).get("name", "Classync member")
    st.session_state.user_username = username or (profile or {}).get("username", "member")


def log_out():
    st.session_state.authenticated = False
    st.session_state.pop("user_email", None)
    st.session_state.pop("user_name", None)
    st.session_state.pop("user_username", None)
