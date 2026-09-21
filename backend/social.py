import base64
import json
import mimetypes
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


DEFAULT_NOTES_ROOT = Path("notes")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
PROFILE_FILENAMES = {"profile.png", "profile.jpg", "profile.jpeg", "profile.webp", "avatar.png", "avatar.jpg", "avatar.jpeg"}


def _notes_root(notes_root: str | Path | None = None) -> Path:
    if notes_root is None:
        return DEFAULT_NOTES_ROOT
    return Path(notes_root)


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _image_metadata_path(user_dir: Path) -> Path:
    return user_dir / ".social.json"


def iter_note_images(notes_root: str | Path | None = None) -> List[Tuple[str, Path]]:
    root = _notes_root(notes_root)
    if not root.exists():
        return []

    items: List[Tuple[str, Path]] = []
    for user_dir in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        if not user_dir.is_dir():
            continue
        for image_path in sorted(user_dir.iterdir(), key=lambda path: path.name.lower()):
            if image_path.is_file() and image_path.name.lower() not in PROFILE_FILENAMES and image_path.suffix.lower() in IMAGE_SUFFIXES:
                items.append((user_dir.name, image_path))
    return items


def get_image_social_metadata(owner_username: str, filename: str, notes_root: str | Path | None = None) -> Dict[str, Any]:
    root = _notes_root(notes_root)
    user_dir = root / owner_username
    if not user_dir.exists():
        return {"likes": 0, "liked_by": [], "saved_by": []}

    metadata = _load_json(_image_metadata_path(user_dir), {})
    image_data = metadata.get(filename, {})
    return {
        "likes": int(image_data.get("likes", 0) or 0),
        "liked_by": list(image_data.get("liked_by", []) or []),
        "saved_by": list(image_data.get("saved_by", []) or []),
    }


def _set_image_social_metadata(owner_username: str, filename: str, payload: Dict[str, Any], notes_root: str | Path | None = None):
    root = _notes_root(notes_root)
    user_dir = root / owner_username
    if not user_dir.exists():
        return payload

    store = _load_json(_image_metadata_path(user_dir), {})
    store[filename] = payload
    _save_json(_image_metadata_path(user_dir), store)
    return payload


def toggle_like(owner_username: str, filename: str, viewer_username: str, notes_root: str | Path | None = None):
    store = get_image_social_metadata(owner_username, filename, notes_root=notes_root)
    liked_by = list(store.get("liked_by", []) or [])
    if viewer_username in liked_by:
        liked_by.remove(viewer_username)
        liked = False
    else:
        liked_by.append(viewer_username)
        liked = True

    payload = {
        "likes": len(liked_by),
        "liked_by": liked_by,
        "saved_by": list(store.get("saved_by", []) or []),
    }
    _set_image_social_metadata(owner_username, filename, payload, notes_root=notes_root)
    return {"liked": liked, "likes": len(liked_by), "liked_by": liked_by, "saved_by": payload["saved_by"]}


def toggle_save(owner_username: str, filename: str, viewer_username: str, notes_root: str | Path | None = None):
    store = get_image_social_metadata(owner_username, filename, notes_root=notes_root)
    saved_by = list(store.get("saved_by", []) or [])
    if viewer_username in saved_by:
        saved_by.remove(viewer_username)
        saved = False
    else:
        saved_by.append(viewer_username)
        saved = True

    payload = {
        "likes": int(store.get("likes", 0) or 0),
        "liked_by": list(store.get("liked_by", []) or []),
        "saved_by": saved_by,
    }
    _set_image_social_metadata(owner_username, filename, payload, notes_root=notes_root)
    return {"saved": saved, "saved_by": saved_by, "likes": payload["likes"], "liked_by": payload["liked_by"]}


def get_user_metrics(username: str, notes_root: str | Path | None = None) -> Dict[str, int]:
    root = _notes_root(notes_root)
    user_dir = root / username
    uploaded_count = 0
    if user_dir.exists():
        uploaded_count = sum(
            1 for item in user_dir.iterdir()
            if item.is_file() and item.name.lower() not in PROFILE_FILENAMES and item.suffix.lower() in IMAGE_SUFFIXES
        )

    saved_count = 0
    liked_count = 0
    for owner_username, image_path in iter_note_images(root):
        metadata = get_image_social_metadata(owner_username, image_path.name, notes_root=root)
        if username in metadata.get("saved_by", []):
            saved_count += 1
        if username in metadata.get("liked_by", []):
            liked_count += 1

    return {
        "uploaded_count": uploaded_count,
        "saved_count": saved_count,
        "liked_count": liked_count,
    }


def get_user_social_summary(username: str, notes_root: str | Path | None = None) -> Dict[str, int]:
    root = _notes_root(notes_root)
    saved_count = 0
    liked_count = 0
    for owner_username, image_path in iter_note_images(root):
        metadata = get_image_social_metadata(owner_username, image_path.name, notes_root=root)
        if username in metadata.get("saved_by", []):
            saved_count += 1
        if username in metadata.get("liked_by", []):
            liked_count += 1
    return {
        "saved_count": saved_count,
        "liked_count": liked_count,
    }


def get_user_social_images(username: str, collection: str, notes_root: str | Path | None = None) -> List[Tuple[str, Path]]:
    if collection not in {"liked", "saved"}:
        raise ValueError("collection must be 'liked' or 'saved'")

    matching_images: List[Tuple[str, Path]] = []
    relation_key = f"{collection}_by"
    for owner_username, image_path in iter_note_images(notes_root):
        metadata = get_image_social_metadata(owner_username, image_path.name, notes_root=notes_root)
        if username in metadata.get(relation_key, []):
            matching_images.append((owner_username, image_path))
    return matching_images


def delete_note_image(owner_username: str, filename: str, notes_root: str | Path | None = None) -> bool:
    safe_filename = Path(filename).name
    if safe_filename != filename or safe_filename.lower() in PROFILE_FILENAMES or Path(safe_filename).suffix.lower() not in IMAGE_SUFFIXES:
        return False

    root = _notes_root(notes_root)
    user_dir = root / owner_username
    image_path = user_dir / safe_filename
    if not image_path.is_file():
        return False

    image_path.unlink()
    for metadata_filename in (".social.json", ".uploaders.json"):
        metadata_path = user_dir / metadata_filename
        metadata = _load_json(metadata_path, {})
        if safe_filename in metadata:
            del metadata[safe_filename]
            _save_json(metadata_path, metadata)
    return True


def save_profile_photo(username: str, uploaded_file, notes_root: str | Path | None = None) -> Path:
    root = _notes_root(notes_root)
    user_dir = root / username
    user_dir.mkdir(parents=True, exist_ok=True)

    for candidate in ["profile.png", "profile.jpg", "profile.jpeg", "profile.webp", "avatar.png", "avatar.jpg", "avatar.jpeg"]:
        existing = user_dir / candidate
        if existing.exists():
            existing.unlink()

    suffix = Path(getattr(uploaded_file, "name", "profile.png")).suffix.lower() or ".png"
    target = user_dir / f"profile{suffix}"
    with target.open("wb") as handle:
        handle.write(uploaded_file.getbuffer())
    return target


def remove_profile_photo(username: str, notes_root: str | Path | None = None) -> bool:
    photo_path = get_profile_photo_path(username, notes_root=notes_root)
    if photo_path is None:
        return False
    photo_path.unlink()
    return True


def get_profile_photo_path(username: str, notes_root: str | Path | None = None) -> Path | None:
    root = _notes_root(notes_root)
    user_dir = root / username
    if not user_dir.exists():
        return None

    for candidate in ["profile.png", "profile.jpg", "profile.jpeg", "profile.webp", "avatar.png", "avatar.jpg", "avatar.jpeg"]:
        path = user_dir / candidate
        if path.exists():
            return path
    return None


def get_profile_photo_data_uri(username: str, notes_root: str | Path | None = None) -> str | None:
    photo_path = get_profile_photo_path(username, notes_root=notes_root)
    if photo_path is None:
        return None
    mime_type = mimetypes.guess_type(photo_path.name)[0] or "image/png"
    image_data = base64.b64encode(photo_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{image_data}"


def get_user_people(notes_root: str | Path | None = None) -> List[Dict[str, Any]]:
    root = _notes_root(notes_root)
    if not root.exists():
        return []

    people: List[Dict[str, Any]] = []
    for username_dir in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        if not username_dir.is_dir():
            continue
        username = username_dir.name
        metrics = get_user_metrics(username, notes_root=root)
        people.append({
            "username": username,
            "metrics": metrics,
            "profile_photo": get_profile_photo_path(username, notes_root=root),
        })
    return people
