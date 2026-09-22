import json
from io import BytesIO

from backend import auth
from backend.requests import create_request, create_response, create_responses, list_requests, list_responses, response_file, save_uploaded_photo


def test_request_can_be_fulfilled_with_an_uploaded_note(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    notes_root = tmp_path / "notes"
    responder_dir = notes_root / "alex"
    responder_dir.mkdir(parents=True)
    (responder_dir / "calculus.pdf").write_bytes(b"pdf content")

    request_id = create_request("sam", "Need calculus revision", "Limits and derivatives", "Mathematics")

    assert request_id is not None
    assert list_requests("open")[0]["title"] == "Need calculus revision"
    assert create_response(request_id, "alex", "calculus.pdf", "This covers the requested unit.") is False

    monkeypatch.chdir(tmp_path)
    assert create_response(request_id, "alex", "calculus.pdf", "This covers the requested unit.") is True
    assert list_requests("open") == []
    fulfilled = list_requests("fulfilled")
    assert fulfilled[0]["status"] == "fulfilled"
    responses = list_responses(request_id)
    assert responses[0]["responder_username"] == "alex"
    assert response_file(responses[0]).name == "calculus.pdf"


def test_request_rejects_internal_and_unsafe_files(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    monkeypatch.chdir(tmp_path)
    notes_dir = tmp_path / "notes" / "alex"
    notes_dir.mkdir(parents=True)
    (notes_dir / ".social.json").write_text(json.dumps({}), encoding="utf-8")
    (notes_dir / "notes.exe").write_bytes(b"no")

    request_id = create_request("sam", "Need notes", "", "General")

    assert create_response(request_id, "alex", ".social.json") is False
    assert create_response(request_id, "alex", "../notes.exe") is False


def test_helper_photo_upload_is_saved_with_a_unique_name(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    monkeypatch.chdir(tmp_path)

    first = BytesIO(b"photo one")
    first.name = "solution.jpg"
    first.size = 9
    second = BytesIO(b"photo two")
    second.name = "solution.jpg"
    second.size = 9

    assert save_uploaded_photo("alex", first).name == "solution.jpg"
    assert save_uploaded_photo("alex", second).name == "solution-2.jpg"
    unsupported = BytesIO(b"bad")
    unsupported.name = "notes.exe"
    assert save_uploaded_photo("alex", unsupported) is None


def test_helper_can_send_multiple_existing_notes_for_one_request(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    monkeypatch.chdir(tmp_path)
    notes_dir = tmp_path / "notes" / "alex"
    notes_dir.mkdir(parents=True)
    (notes_dir / "page-one.jpg").write_bytes(b"one")
    (notes_dir / "page-two.jpg").write_bytes(b"two")

    request_id = create_request("sam", "Need the full chapter", "", "Science")

    assert create_responses(request_id, "alex", ["page-one.jpg", "page-two.jpg"], "Here are both pages.") is True
    assert [item["filename"] for item in list_responses(request_id)] == ["page-two.jpg", "page-one.jpg"]
