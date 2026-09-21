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
from backend.social import PROFILE_FILENAMES, delete_note_image, get_image_social_metadata, get_user_social_summary, iter_note_images, toggle_like, toggle_save
from backend.study import load_study_plan, save_study_plan
from backend.admin import log_activity
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Notes", layout="wide", initial_sidebar_state="expanded")
require_auth()
render_sidebar("notes")

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
DEFAULT_CATEGORIES = [
    "Mathematics",
    "Science",
    "Computer Science",
    "Languages",
    "History",
    "Business",
    "Exam Revision",
    "Projects",
    "Uncategorized",
]


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
    safe_title = html.escape(details.get("title", ""))
    safe_tags = html.escape(details.get("tags", ""))
    safe_category = html.escape(details.get("category", "Uncategorized"))
    initials = "".join(part[0] for part in safe_name.split()[:2]).upper() or "C"
    title_markup = f'<strong class="note_title">{safe_title}</strong>' if safe_title else ""
    tags_markup = f'<span class="note_tags">{safe_tags}</span>' if safe_tags else ""
    category_markup = f'<span class="note_category">{safe_category}</span>'
    return (
        f'<div class="uploader_details">'
        f'<div class="uploader_identity">'
        f'<span class="uploader_avatar">{html.escape(initials)}</span>'
        f'<div>{title_markup}<strong>{safe_name}</strong><span class="uploader_username">@{safe_username}</span>{category_markup}{tags_markup}</div>'
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

st.markdown(
    """
    <div class="notes_hero">
        <div>
            <span class="eyebrow">YOUR NOTEBOOK</span>
            <h1>Notes that feel alive.</h1>
            <p>Keep your learning organized, polished, and share-ready.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

current_username = st.session_state.get("user_username", "member")
MAX_NOTE_UPLOAD_BYTES = 10 * 1024 * 1024
if "custom_note_categories" not in st.session_state:
    st.session_state.custom_note_categories = []


def available_categories():
    categories = set(DEFAULT_CATEGORIES)
    notes_root = path.Path("notes")
    if notes_root.exists():
        for metadata_path in notes_root.glob("*/.uploaders.json"):
            for details in load_upload_metadata(metadata_path.parent).values():
                category = str(details.get("category", "")).strip()
                if category:
                    categories.add(category)
    categories.update(st.session_state.custom_note_categories)
    return sorted(categories, key=str.casefold)


public_notes_root = path.Path("notes")
total_images = 0
if public_notes_root.exists():
    total_images = sum(1 for item in public_notes_root.rglob("*") if item.is_file() and item.name.lower() not in PROFILE_FILENAMES and item.suffix.lower() in IMAGE_SUFFIXES)
user_social_summary = get_user_social_summary(current_username)

stats_cols = st.columns(3)
with stats_cols[0]:
    st.markdown(f'<div class="small_stat"><span>Total notes</span><strong>{total_images}</strong></div>', unsafe_allow_html=True)
with stats_cols[1]:
    st.markdown(f'<div class="small_stat"><span>Saved</span><strong>{user_social_summary["saved_count"]}</strong></div>', unsafe_allow_html=True)
with stats_cols[2]:
    st.markdown(f'<div class="small_stat"><span>Liked</span><strong>{user_social_summary["liked_count"]}</strong></div>', unsafe_allow_html=True)

col_upload, col_find = st.columns([1.1, 1.9])
with col_upload:
    st.markdown('<div class="panel"><h3>Upload a note</h3>', unsafe_allow_html=True)
    note_title = st.text_input("Note title", placeholder="e.g. Cell biology - lecture 04", label_visibility="collapsed")
    note_tags = st.text_input("Study tags", placeholder="Tags: biology, exam, revision", label_visibility="collapsed")
    note_category = st.selectbox("Note category", available_categories(), key="note_category")
    with st.expander("Add a new category"):
        custom_category = st.text_input("New category", placeholder="e.g. Psychology", key="custom_note_category_input")
        if st.button("Add category", key="add_note_category", use_container_width=True):
            normalized_category = custom_category.strip()[:50]
            if normalized_category and normalized_category.casefold() not in {category.casefold() for category in available_categories()}:
                st.session_state.custom_note_categories.append(normalized_category)
                st.session_state.note_category = normalized_category
                st.rerun()
            elif not normalized_category:
                st.warning("Enter a category name first.")
            else:
                st.info("That category already exists.")
    uploaded_file = st.file_uploader("Choose a file", type=["image"], key="image_uploader", label_visibility="collapsed")
    if uploaded_file is not None:
        if uploaded_file.size > MAX_NOTE_UPLOAD_BYTES:
            st.error("Notes must be 10 MB or smaller.")
            st.stop()
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
            "title": note_title.strip()[:100],
            "tags": note_tags.strip()[:160],
            "category": note_category,
        }
        save_upload_metadata(notes_dir, metadata)
        log_activity(current_username, "upload_note", safe_filename, note_category)
        st.success(f"Uploaded '{uploaded_file.name}' successfully.")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_find:
    st.markdown('<div class="panel"><h3>Find your notes</h3>', unsafe_allow_html=True)
    search_query = st.text_input("Search notes", placeholder="Filter by filename, name, or username", label_visibility="collapsed")
    category_filter = st.selectbox("Filter by category", ["All categories"] + available_categories(), key="note_category_filter")
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Build a quick study plan"):
    if "study_plan" not in st.session_state:
        st.session_state.study_plan = load_study_plan(current_username)
    with st.form("study_plan_form"):
        plan_focus = st.text_input("Study focus", value=st.session_state.study_plan["focus"], placeholder="e.g. Prepare for Friday's chemistry quiz")
        plan_date = st.date_input("Target date", value=st.session_state.study_plan["date"])
        plan_cols = st.columns(3)
        plan_tasks = []
        for index, column in enumerate(plan_cols):
            with column:
                plan_tasks.append(st.text_input(f"Task {index + 1}", value=st.session_state.study_plan["tasks"][index], placeholder="One small next step"))
        if st.form_submit_button("Save study plan", type="primary", use_container_width=True):
            st.session_state.study_plan = {"focus": plan_focus.strip(), "tasks": plan_tasks, "date": plan_date}
            save_study_plan(current_username, plan_focus, plan_tasks, plan_date)
            st.success("Study plan saved.")
    saved_plan = st.session_state.study_plan
    if saved_plan["focus"]:
        st.markdown(f'**{html.escape(saved_plan["focus"])}** · target {saved_plan["date"].strftime("%b %d, %Y")}')
        for index, task in enumerate(saved_plan["tasks"]):
            if task:
                st.checkbox(task, key=f"study_plan_task_{index}")

st.markdown('<div class="gallery_header"><h2>Public notes album</h2></div>', unsafe_allow_html=True)

public_album = []
public_notes_root = path.Path("notes")
if public_notes_root.exists():
    for owner_dir in public_notes_root.iterdir():
        if not owner_dir.is_dir():
            continue
        metadata = load_upload_metadata(owner_dir)
        for image_file in owner_dir.iterdir():
            if image_file.is_file() and image_file.name.lower() not in PROFILE_FILENAMES and image_file.suffix.lower() in IMAGE_SUFFIXES:
                public_album.append({
                    "path": image_file,
                    "owner_username": owner_dir.name,
                    "details": uploader_details(metadata, image_file.name, owner_dir.name),
                })

if search_query:
    normalized_query = search_query.lower()
    public_album = [
        item for item in public_album
        if normalized_query in item["path"].name.lower()
        or normalized_query in item["details"]["name"].lower()
        or normalized_query in item["details"]["username"].lower()
        or normalized_query in item["details"].get("title", "").lower()
        or normalized_query in item["details"].get("tags", "").lower()
    ]

if category_filter != "All categories":
    public_album = [
        item for item in public_album
        if item["details"].get("category", "Uncategorized") == category_filter
    ]

public_album.sort(key=lambda item: item["path"].stat().st_mtime, reverse=True)

if public_album:
    for index in range(0, len(public_album), 3):
        cols = st.columns(3)
        for offset, col in enumerate(cols):
            item = public_album[index + offset] if index + offset < len(public_album) else None
            if item is None:
                continue
            with col:
                st.image(str(item["path"]), use_container_width=True)
                st.markdown(uploader_markup(item["details"]), unsafe_allow_html=True)
                meta = get_image_social_metadata(item["owner_username"], item["path"].name)
                liked = st.session_state.get("user_username", "") in meta.get("liked_by", [])
                saved = st.session_state.get("user_username", "") in meta.get("saved_by", [])
                st.markdown(
                    f"""
                    <div class="social_row">
                        <span>{len(meta.get('liked_by', []))} likes</span>
                        <span>{len(meta.get('saved_by', []))} saves</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                like_col, save_col = st.columns(2)
                with like_col:
                    if st.button("Like" if not liked else "Liked", key=f"notes_like_{item['owner_username']}_{item['path'].name}", use_container_width=True):
                        toggle_like(item["owner_username"], item["path"].name, st.session_state.get("user_username", ""))
                        st.rerun()
                with save_col:
                    if st.button("Save" if not saved else "Saved", key=f"notes_save_{item['owner_username']}_{item['path'].name}", use_container_width=True):
                        toggle_save(item["owner_username"], item["path"].name, st.session_state.get("user_username", ""))
                        st.rerun()
                if item["owner_username"] == st.session_state.get("user_username"):
                    confirm_delete = st.checkbox("Confirm delete", key=f"confirm_delete_{item['owner_username']}_{item['path'].name}")
                    if st.button("Delete", key=f"delete_{item['owner_username']}_{item['path'].name}", use_container_width=True, disabled=not confirm_delete):
                        if delete_note_image(item["owner_username"], item["path"].name):
                            log_activity(current_username, "delete_note", f"{item['owner_username']}/{item['path'].name}")
                            st.rerun()
                st.markdown('<div class="card_divider"></div>', unsafe_allow_html=True)
else:
    st.info("No notes have been shared yet. Upload the first note to start your community collection.")

render_app_footer()
