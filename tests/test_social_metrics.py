import json
from pathlib import Path

from backend.social import delete_note_image, get_user_metrics, get_user_social_images, iter_note_images, toggle_like, toggle_save


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_user_metrics_count_uploaded_and_saved(tmp_path):
    notes_root = tmp_path / "notes"
    alice_dir = notes_root / "alice"
    bob_dir = notes_root / "bob"
    alice_dir.mkdir(parents=True, exist_ok=True)
    bob_dir.mkdir(parents=True, exist_ok=True)

    (alice_dir / "a.png").write_bytes(b"a")
    (alice_dir / "b.png").write_bytes(b"b")
    (bob_dir / "c.png").write_bytes(b"c")

    _write_json(
        alice_dir / ".uploaders.json",
        {
            "a.png": {"name": "Alice", "username": "alice", "email": "alice@example.com", "uploaded_at": "Today"},
            "b.png": {"name": "Alice", "username": "alice", "email": "alice@example.com", "uploaded_at": "Today"},
        },
    )
    _write_json(
        bob_dir / ".uploaders.json",
        {"c.png": {"name": "Bob", "username": "bob", "email": "bob@example.com", "uploaded_at": "Today"}},
    )

    toggle_save("bob", "c.png", "alice", notes_root=notes_root)
    toggle_like("bob", "c.png", "alice", notes_root=notes_root)
    toggle_like("bob", "c.png", "alice", notes_root=notes_root)

    metrics = get_user_metrics("alice", notes_root=notes_root)

    assert metrics["uploaded_count"] == 2
    assert metrics["saved_count"] == 1
    assert metrics["liked_count"] == 0


def test_toggle_save_and_like_work_for_an_image(tmp_path):
    notes_root = tmp_path / "notes"
    user_dir = notes_root / "charlie"
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "post.jpg").write_bytes(b"img")

    saved = toggle_save("charlie", "post.jpg", "dana", notes_root=notes_root)
    liked = toggle_like("charlie", "post.jpg", "dana", notes_root=notes_root)

    assert saved["saved_by"] == ["dana"]
    assert liked["liked_by"] == ["dana"]
    assert liked["likes"] == 1


def test_user_social_images_returns_liked_and_saved_grids(tmp_path):
    notes_root = tmp_path / "notes"
    owner_dir = notes_root / "owner"
    owner_dir.mkdir(parents=True)
    (owner_dir / "liked.png").write_bytes(b"liked")
    (owner_dir / "saved.png").write_bytes(b"saved")

    toggle_like("owner", "liked.png", "viewer", notes_root=notes_root)
    toggle_save("owner", "saved.png", "viewer", notes_root=notes_root)

    assert [path.name for _, path in get_user_social_images("viewer", "liked", notes_root)] == ["liked.png"]
    assert [path.name for _, path in get_user_social_images("viewer", "saved", notes_root)] == ["saved.png"]


def test_delete_note_image_removes_file_and_metadata_but_not_profile_photo(tmp_path):
    notes_root = tmp_path / "notes"
    owner_dir = notes_root / "owner"
    owner_dir.mkdir(parents=True)
    (owner_dir / "lesson.png").write_bytes(b"lesson")
    (owner_dir / "profile.png").write_bytes(b"profile")
    _write_json(owner_dir / ".social.json", {"lesson.png": {"liked_by": ["viewer"]}})
    _write_json(owner_dir / ".uploaders.json", {"lesson.png": {"name": "Owner"}})

    assert delete_note_image("owner", "lesson.png", notes_root)
    assert not (owner_dir / "lesson.png").exists()
    assert "lesson.png" not in json.loads((owner_dir / ".social.json").read_text())
    assert "lesson.png" not in json.loads((owner_dir / ".uploaders.json").read_text())
    assert (owner_dir / "profile.png").exists()
    assert [(owner, path.name) for owner, path in iter_note_images(notes_root)] == []
