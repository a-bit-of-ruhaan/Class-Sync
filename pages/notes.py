import base64
import datetime
import html
import json

import streamlit as st
import pathlib as path

from backend.auth import (
    get_user_notes_directory,
    get_user_profile_by_username,
    require_auth,
)


st.set_page_config(
    page_title="NOTES",
    layout="wide"
)

require_auth()

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def load_upload_metadata(notes_dir):
    metadata_path = notes_dir / ".uploaders.json"
    if not metadata_path.exists():
        return {}
    try:
        with metadata_path.open(encoding="utf-8") as metadata_file:
            return json.load(metadata_file)
    except (OSError, json.JSONDecodeError):
        return {}


def save_upload_metadata(notes_dir, metadata):
    metadata_path = notes_dir / ".uploaders.json"
    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)


def uploader_details(metadata, filename, owner_username):
    details = metadata.get(filename)
    if details:
        return details
    profile = get_user_profile_by_username(owner_username) or {}
    return {
        "name": profile.get("name", "Classync member"),
        "username": profile.get("username", owner_username),
        "email": profile.get("email", ""),
        "uploaded_at": "Earlier upload",
    }


def uploader_markup(details):
    safe_name = html.escape(details.get("name", "Classync member"))
    safe_username = html.escape(details.get("username", "member"))
    safe_email = html.escape(details.get("email", ""))
    safe_uploaded_at = html.escape(details.get("uploaded_at", "Earlier upload"))
    initials = "".join(part[0] for part in safe_name.split()[:2]).upper() or "C"
    return (
        f'<div class="uploader_details">'
        f'<div class="uploader_identity">'
        f'<span class="uploader_avatar">{html.escape(initials)}</span>'
        f'<div><strong>{safe_name}</strong><span class="uploader_username">@{safe_username}</span></div>'
        f'</div>'
        f'<div class="uploader_contact">{safe_email}</div>'
        f'<div class="uploader_time">Uploaded {safe_uploaded_at}</div>'
        f'</div>'
    )

with open("styles/notes.css") as f:
    page_css = f.read()
with open("images/backg.png", "rb") as f:
    background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)

st.markdown("""<div class="header_main">
                <h1>Find Your Notes</h1>
                <p>Get useful notes or upload your own</p>
            </div>""", unsafe_allow_html=True)

col_upload,  col_find = st.columns([1, 2])

with col_upload:
    st.subheader("Upload Your Notes")
    uploaded_file = st.file_uploader("Choose a file", type=["image"], key="image_uploader")
    if uploaded_file is not None:
        notes_dir = get_user_notes_directory()
        safe_filename = path.Path(uploaded_file.name).name
        file_path = notes_dir / safe_filename
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        metadata = load_upload_metadata(notes_dir)
        metadata[safe_filename] = {
            "name": st.session_state.get("user_name", "Classync member"),
            "username": st.session_state.get("user_username", "member"),
            "email": st.session_state.get("user_email", ""),
            "uploaded_at": datetime.datetime.now().astimezone().strftime("%b %d, %Y at %I:%M %p"),
        }
        save_upload_metadata(notes_dir, metadata)
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")

 

with col_find:
    col_finder, col_img = st.columns([2,1])

    with col_finder:
        st.subheader("Find Your Notes")
        search_query = st.text_input("Search notes", placeholder="Filter by filename", label_visibility="collapsed")
        selected_note = None

    with col_img:
        st.info("Browse the public album below to view uploaded notes.")

st.markdown('<div class="image_grid">', unsafe_allow_html=True)
st.markdown('<h2>Public Notes Album</h2>', unsafe_allow_html=True)
st.markdown('<p class="album_intro">Explore notes shared by everyone in Classync.</p>', unsafe_allow_html=True)

public_album = []
public_notes_root = path.Path("notes")
if public_notes_root.exists():
    for owner_dir in public_notes_root.iterdir():
        if not owner_dir.is_dir():
            continue
        metadata = load_upload_metadata(owner_dir)
        for image_file in owner_dir.iterdir():
            if image_file.is_file() and image_file.suffix.lower() in IMAGE_SUFFIXES:
                public_album.append(
                    {
                        "path": image_file,
                        "owner_username": owner_dir.name,
                        "details": uploader_details(metadata, image_file.name, owner_dir.name),
                    }
                )

if search_query:
    normalized_query = search_query.lower()
    public_album = [
        item for item in public_album
        if normalized_query in item["path"].name.lower()
        or normalized_query in item["details"]["name"].lower()
        or normalized_query in item["details"]["username"].lower()
    ]

public_album.sort(key=lambda item: item["path"].stat().st_mtime, reverse=True)
if public_album:
    st.caption(f"{len(public_album)} shared image{'s' if len(public_album) != 1 else ''}")
    cols_per_row = 5
    for index in range(0, len(public_album), cols_per_row):
        cols = st.columns(cols_per_row)
        for column_index, col in enumerate(cols):
            album_index = index + column_index
            if album_index < len(public_album):
                item = public_album[album_index]
                with col:
                    st.image(str(item["path"]), caption=item["path"].name, use_container_width=True)
                    st.markdown(uploader_markup(item["details"]), unsafe_allow_html=True)
                    if item["owner_username"] == st.session_state.get("user_username"):
                        if st.button("Delete", key=f"delete_{item['owner_username']}_{item['path'].name}", icon=":material/delete:"):
                            item["path"].unlink(missing_ok=True)
                            st.rerun()
else:
    st.info("No images have been shared yet. Upload the first note to the public album.")

st.markdown('</div>', unsafe_allow_html=True)