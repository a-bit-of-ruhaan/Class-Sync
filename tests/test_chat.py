from backend import auth
from backend.chat import (
    create_direct_conversation,
    create_group_conversation,
    get_mate_status,
    get_messages,
    get_unread_count,
    list_conversations,
    mark_conversation_read,
    respond_to_mate_request,
    send_mate_request,
    send_message,
)


def test_direct_chat_tracks_messages_and_unread_state(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    assert auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")[0]
    assert auth.register_user("Sam Lee", "sam", "sam@example.com", "password123")[0]

    assert send_mate_request("alex", "sam")
    assert get_mate_status("sam", "alex")["status"] == "received"
    request_id = get_mate_status("sam", "alex")["request_id"]
    assert respond_to_mate_request(request_id, "sam", True)
    assert get_mate_status("alex", "sam")["status"] == "mates"
    conversation_id = create_direct_conversation("alex", "sam")
    assert conversation_id is not None
    assert send_message(conversation_id, "alex", "Want to revise together?")
    assert get_unread_count("sam") == 1
    assert get_messages(conversation_id, "sam")[0]["body"] == "Want to revise together?"

    mark_conversation_read(conversation_id, "sam")
    assert get_unread_count("sam") == 0


def test_group_chat_adds_members_and_rejects_invalid_message_sender(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    for name, username in (("Alex Morgan", "alex"), ("Sam Lee", "sam"), ("Jo Kim", "joe")):
        assert auth.register_user(name, username, f"{username}@example.com", "password123")[0]

    conversation_id = create_group_conversation("alex", "Study crew", ["sam", "joe"])
    assert conversation_id is not None
    assert len(list_conversations("sam")) == 1
    assert send_message(conversation_id, "sam", "Hello everyone")
    assert not send_message(conversation_id, "outsider", "No access")


def test_direct_chat_requires_accepted_mates(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    assert auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")[0]
    assert auth.register_user("Sam Lee", "sam", "sam@example.com", "password123")[0]
    assert create_direct_conversation("alex", "sam") is None
    assert send_mate_request("alex", "sam")
    assert create_direct_conversation("alex", "sam") is None