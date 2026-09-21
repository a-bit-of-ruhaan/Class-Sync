from backend import auth
from backend.admin import is_admin, list_activity, set_user_banned


def test_admin_ban_updates_user_and_audits_action(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    assert auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")[0]
    monkeypatch.setenv("ADMIN_EMAILS", "dev@example.com")

    assert is_admin("DEV@example.com")
    assert set_user_banned("alex", True, "developer")
    assert auth.get_user_profile_by_username("alex")["banned"] == 1
    assert list_activity(10)[0]["action"] == "ban_user"