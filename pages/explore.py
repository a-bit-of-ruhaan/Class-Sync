import base64
import html

import streamlit as st

from backend.auth import get_user_profile_by_username, require_auth
from backend.social import get_image_social_metadata, get_user_people, iter_note_images, toggle_like, toggle_save
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Explore", layout="wide", initial_sidebar_state="expanded")
require_auth()
render_sidebar("explore")

with open("styles/explore.css", encoding="utf-8") as f:
    page_css = f.read()
with open("images/backg.png", "rb") as f:
    background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)


def get_initials(name: str):
    parts = [part for part in name.strip().split() if part]
    if not parts:
        return "C"
    initials = "".join(part[0].upper() for part in parts[:2])
    return initials or "C"


user_name = st.session_state.get("user_name", "Classync member")
user_username = st.session_state.get("user_username", "member")

st.markdown(
    """
    <div class="page_header">
        <div>
            <span class="eyebrow">DISCOVER</span>
            <h1>Explore Classync</h1>
            <p>Browse creative work from fellow learners and keep an eye on the people shaping the community.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

people = get_user_people()
if people:
    st.markdown('<div class="people_row">', unsafe_allow_html=True)
    for person in people:
        username = person["username"]
        metrics = person["metrics"]
        profile_record = get_user_profile_by_username(username) or {}
        if not profile_record.get("discoverable", 1):
            continue
        display_name = profile_record.get("name") or username.title()
        avatar = person.get("profile_photo")
        if avatar:
            profile_html = f'<img class="mini_avatar" src="{avatar}" alt="{username}" />'
        else:
            initials = get_initials(display_name)
            profile_html = f'<div class="mini_avatar no_photo">{html.escape(initials)}</div>'

        st.markdown(
            f"""
            <div class="person_card">
                <div class="person_top">
                    {profile_html}
                    <div>
                        <strong>{html.escape(display_name)}</strong>
                        <span>@{html.escape(username)}</span>
                    </div>
                </div>
                <div class="mini_stats">
                    <div><span>{metrics['uploaded_count']}</span> uploads</div>
                    <div><span>{metrics['saved_count']}</span> saved</div>
                    <div><span>{metrics['liked_count']}</span> likes</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"View {display_name}'s profile", key=f"explore_profile_{username}", use_container_width=True):
            st.session_state["profile_username"] = username
            st.switch_page("pages/profile.py")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="feed_header"><h2>Recent community notes</h2></div>', unsafe_allow_html=True)

note_items = iter_note_images()
if not note_items:
    st.info("No notes uploaded yet. Your community gallery will appear here once someone shares a note.")
else:
    cols = st.columns(3)
    for index, (owner_username, image_path) in enumerate(note_items):
        with cols[index % 3]:
            image_metadata = get_image_social_metadata(owner_username, image_path.name)
            liked = st.session_state.get("user_username", "") in image_metadata.get("liked_by", [])
            saved = st.session_state.get("user_username", "") in image_metadata.get("saved_by", [])

            st.image(str(image_path), use_container_width=True)
            st.markdown(
                f"""
                <div class="note_meta">
                    <div class="note_owner">
                        <span class="mini_avatar tiny">{html.escape(get_initials(owner_username))}</span>
                        <div>
                            <strong>{html.escape(owner_username)}</strong>
                            <span>{image_path.name}</span>
                        </div>
                    </div>
                    <div class="note_actions">
                        <span>{len(image_metadata.get('liked_by', []))} likes</span>
                        <span>{len(image_metadata.get('saved_by', []))} saves</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Like" if not liked else "Liked", key=f"explore_like_{owner_username}_{image_path.name}", use_container_width=True):
                    toggle_like(owner_username, image_path.name, user_username)
                    st.rerun()
            with action_col2:
                if st.button("Save" if not saved else "Saved", key=f"explore_save_{owner_username}_{image_path.name}", use_container_width=True):
                    toggle_save(owner_username, image_path.name, user_username)
                    st.rerun()

            if st.button(f"View {owner_username}'s profile", key=f"profile_{owner_username}_{image_path.name}", use_container_width=True):
                st.session_state["profile_username"] = owner_username
                st.switch_page("pages/profile.py")

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

render_app_footer()
