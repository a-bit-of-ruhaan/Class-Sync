from backend import auth
from unittest.mock import Mock


def test_update_user_profile_persists_social_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    created, _ = auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")
    assert created

    updated, message = auth.update_user_profile(
        "alex@example.com",
        "Alex M.",
        "Learning in public.",
        "they/them",
        "London",
        "alex.dev",
        "alexmorgan",
        "alex.learns",
        False,
    )

    assert updated
    assert message == "Profile updated."
    profile = auth.get_user_profile_by_username("alex")
    assert profile["name"] == "Alex M."
    assert profile["bio"] == "Learning in public."
    assert profile["github"] == "alexmorgan"
    assert profile["discoverable"] == 0


def test_restore_session_rehydrates_from_cookie(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    created, _ = auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")
    assert created
    token = auth._create_login_session("alex@example.com")

    fake_streamlit = Mock()
    fake_streamlit.session_state = {}
    fake_streamlit.query_params = {}
    cookie_manager = Mock()
    cookie_manager.get.return_value = token
    monkeypatch.setattr(auth, "st", fake_streamlit)
    monkeypatch.setattr(auth, "_cookie_manager", cookie_manager)
    login = Mock()
    monkeypatch.setattr(auth, "log_in", login)

    assert auth.restore_session() is True
    login.assert_called_once_with("alex@example.com", create_session=False)


def test_log_out_revokes_cookie_only_session(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    created, _ = auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")
    assert created
    token = auth._create_login_session("alex@example.com")

    class SessionState(dict):
        def __getattr__(self, name):
            return self.get(name)

        def __setattr__(self, name, value):
            self[name] = value

    fake_streamlit = Mock()
    fake_streamlit.session_state = SessionState(authenticated=True, user_email="alex@example.com")
    fake_streamlit.query_params = {}
    cookie_manager = Mock()
    cookie_manager.get.return_value = token
    monkeypatch.setattr(auth, "st", fake_streamlit)
    monkeypatch.setattr(auth, "_cookie_manager", cookie_manager)

    auth.log_out()

    connection = auth._connect()
    try:
        assert connection.execute("SELECT 1 FROM login_sessions WHERE token_hash = ?", (auth._session_token_hash(token),)).fetchone() is None
    finally:
        connection.close()


def test_search_user_profiles_matches_name_username_and_hides_private_users(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    assert auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")[0]
    assert auth.register_user("Biology Buddy", "bio_buddy", "bio@example.com", "password123")[0]
    assert auth.register_user("Private Learner", "private_user", "private@example.com", "password123")[0]
    auth.update_user_profile("alex@example.com", "Alex Morgan", "Physics and revision")
    auth.update_user_profile("private@example.com", "Private Learner", "Physics", discoverable=False)

    assert [user["username"] for user in auth.search_user_profiles("physics")] == ["alex"]
    assert auth.search_user_profiles("private") == []