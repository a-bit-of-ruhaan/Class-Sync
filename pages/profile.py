import base64
import html

import streamlit as st

from backend.auth import get_user_profile_by_username, require_auth, update_user_profile
from backend.chat import get_mate_status, list_mate_requests, list_mates, remove_mate, respond_to_mate_request, send_mate_request
from backend.social import delete_note_image, get_image_social_metadata, get_profile_photo_data_uri, get_profile_photo_path, get_user_metrics, get_user_social_images, iter_note_images, remove_profile_photo, save_profile_photo, toggle_like, toggle_save
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Profile", layout="wide", initial_sidebar_state="expanded")
require_auth()
render_sidebar("profile")

with open("styles/profile.css", encoding="utf-8") as f:
    page_css = f.read()
with open("images/backg.png", "rb") as f:
    background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)


def initials_for(value: str):
    parts = [part for part in value.split() if part]
    if not parts:
        return "C"
    initials = "".join(part[0].upper() for part in parts[:2])
    return initials or "C"


selected_user = st.session_state.get("profile_username") or st.session_state.get("user_username", "member")
profile_record = get_user_profile_by_username(selected_user) or {}
user_name = profile_record.get("name") or st.session_state.get("user_name", selected_user.title())
profile_photo = get_profile_photo_path(selected_user)
profile_photo_uri = get_profile_photo_data_uri(selected_user)
is_own_profile = selected_user == st.session_state.get("user_username")
viewer_username = st.session_state.get("user_username", "")

if profile_photo:
    avatar_html = f'<img class="profile_avatar" src="{profile_photo_uri}" alt="{html.escape(selected_user)}" />'
else:
    avatar_html = f'<div class="profile_avatar placeholder">{html.escape(initials_for(user_name or selected_user))}</div>'

metrics = get_user_metrics(selected_user)

st.markdown(
    f"""
    <div class="profile_header">
        {avatar_html}
        <div class="profile_meta">
            <span class="eyebrow">PROFILE</span>
            <h1>{html.escape(user_name)}</h1>
            <p>@{html.escape(selected_user)}</p>
            <p class="profile_bio">{html.escape(profile_record.get("bio", ""))}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if profile_record.get("pronouns") or profile_record.get("location") or profile_record.get("website") or profile_record.get("github") or profile_record.get("instagram"):
    profile_details = []
    if profile_record.get("pronouns"):
        profile_details.append(f'<span>{html.escape(profile_record["pronouns"])}</span>')
    if profile_record.get("location"):
        profile_details.append(f'<span>{html.escape(profile_record["location"])}</span>')
    if profile_record.get("website"):
        website = profile_record["website"]
        href = website if website.startswith(("http://", "https://")) else f"https://{website}"
        profile_details.append(f'<a href="{html.escape(href, quote=True)}" target="_blank">{html.escape(website)}</a>')
    if profile_record.get("github"):
        github = profile_record["github"]
        profile_details.append(f'<a href="https://github.com/{html.escape(github, quote=True)}" target="_blank">GitHub / {html.escape(github)}</a>')
    if profile_record.get("instagram"):
        instagram = profile_record["instagram"]
        profile_details.append(f'<a href="https://instagram.com/{html.escape(instagram, quote=True)}" target="_blank">Instagram / {html.escape(instagram)}</a>')
    st.markdown(f'<div class="profile_details">{"".join(profile_details)}</div>', unsafe_allow_html=True)

if is_own_profile:
    mate_requests = list_mate_requests(viewer_username)
    if mate_requests:
        with st.expander(f"Mate requests ({len(mate_requests)})", expanded=True):
            for request in mate_requests:
                request_col, accept_col, decline_col = st.columns([2, 1, 1])
                with request_col:
                    st.markdown(f'**{html.escape(request["name"])}** (@{html.escape(request["sender_username"])}) wants to be your mate.')
                with accept_col:
                    if st.button("Accept", key=f"accept_mate_{request['id']}", use_container_width=True):
                        respond_to_mate_request(request["id"], viewer_username, True)
                        st.rerun()
                with decline_col:
                    if st.button("Decline", key=f"decline_mate_{request['id']}", use_container_width=True):
                        respond_to_mate_request(request["id"], viewer_username, False)
                        st.rerun()
else:
    mate_status = get_mate_status(viewer_username, selected_user)
    if mate_status["status"] == "none":
        if st.button("Send mate request", key=f"send_mate_{selected_user}", type="primary", use_container_width=True):
            send_mate_request(viewer_username, selected_user)
            st.success("Mate request sent.")
            st.rerun()
    elif mate_status["status"] == "sent":
        st.info("Mate request sent. Waiting for a response.")
    elif mate_status["status"] == "received":
        accept_col, decline_col = st.columns(2)
        with accept_col:
            if st.button("Accept mate request", key=f"accept_profile_mate_{mate_status['request_id']}", use_container_width=True):
                respond_to_mate_request(mate_status["request_id"], viewer_username, True)
                st.rerun()
        with decline_col:
            if st.button("Decline request", key=f"decline_profile_mate_{mate_status['request_id']}", use_container_width=True):
                respond_to_mate_request(mate_status["request_id"], viewer_username, False)
                st.rerun()
    elif mate_status["status"] == "mates":
        confirm_remove = st.checkbox("Confirm removing this mate", key=f"confirm_remove_mate_{selected_user}")
        if st.button("Remove mate", key=f"remove_mate_{selected_user}", use_container_width=True, disabled=not confirm_remove):
            remove_mate(viewer_username, selected_user)
            st.rerun()

profile_mates = list_mates(selected_user)
st.markdown('<div class="mate_list_header"><h2>Mates</h2><span>Public list</span></div>', unsafe_allow_html=True)
if not profile_mates:
    st.caption("No mates to show yet.")
else:
    mate_columns = st.columns(min(3, len(profile_mates)))
    for index, mate in enumerate(profile_mates):
        with mate_columns[index % len(mate_columns)]:
            if st.button(f'{mate["name"]}\n@{mate["username"]}', key=f"profile_mate_{selected_user}_{mate['username']}", use_container_width=True):
                st.session_state["profile_username"] = mate["username"]
                st.rerun()

if is_own_profile:
    with st.expander("Edit your profile", expanded=False):
        with st.form("profile_edit_form"):
            edit_name = st.text_input("Display name", value=profile_record.get("name", ""), max_chars=80)
            edit_bio = st.text_area("Bio", value=profile_record.get("bio", ""), max_chars=280, placeholder="What are you learning or making?")
            edit_col1, edit_col2 = st.columns(2)
            with edit_col1:
                edit_pronouns = st.text_input("Pronouns", value=profile_record.get("pronouns", ""), max_chars=40)
                edit_location = st.text_input("Location", value=profile_record.get("location", ""), max_chars=80)
                edit_website = st.text_input("Website", value=profile_record.get("website", ""), max_chars=200, placeholder="your-site.com")
            with edit_col2:
                edit_github = st.text_input("GitHub username", value=profile_record.get("github", ""), max_chars=39)
                edit_instagram = st.text_input("Instagram username", value=profile_record.get("instagram", ""), max_chars=30)
                edit_discoverable = st.checkbox("Show me in Explore", value=bool(profile_record.get("discoverable", 1)))
            if st.form_submit_button("Save profile", type="primary", use_container_width=True):
                updated, message = update_user_profile(
                    st.session_state.get("user_email", ""), edit_name, edit_bio, edit_pronouns,
                    edit_location, edit_website, edit_github, edit_instagram, edit_discoverable,
                )
                if updated:
                    st.session_state.user_name = edit_name.strip()
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown('<div class="profile_photo_action"><h3>Profile picture</h3><p>Choose a new image for your profile.</p></div>', unsafe_allow_html=True)
    uploaded_photo = st.file_uploader(
        "Upload a new profile picture",
        type=["png", "jpg", "jpeg", "webp"],
        key="profile_photo_uploader",
        label_visibility="collapsed",
    )
    if uploaded_photo is not None:
        save_profile_photo(selected_user, uploaded_photo)
        st.success("Profile photo updated.")
        st.rerun()
    confirm_photo_removal = st.checkbox("Confirm removing profile photo", key="confirm_profile_photo_removal")
    if profile_photo and st.button("Remove profile photo", key="remove_profile_photo", disabled=not confirm_photo_removal):
        remove_profile_photo(selected_user)
        st.rerun()

stats_cols = st.columns(3)
with stats_cols[0]:
    st.markdown('<div class="metric_card"><span>Uploads</span><strong>{}</strong></div>'.format(metrics["uploaded_count"]), unsafe_allow_html=True)
with stats_cols[1]:
    st.markdown('<div class="metric_card"><span>Saved</span><strong>{}</strong></div>'.format(metrics["saved_count"]), unsafe_allow_html=True)
with stats_cols[2]:
    st.markdown('<div class="metric_card"><span>Liked</span><strong>{}</strong></div>'.format(metrics["liked_count"]), unsafe_allow_html=True)

def render_image_grid(images, empty_message, key_prefix):
    if not images:
        st.info(empty_message)
        return

    viewer_username = st.session_state.get("user_username", "")
    grid_cols = st.columns(3)
    for index, (owner_username, image_path) in enumerate(images):
        with grid_cols[index % 3]:
            st.image(str(image_path), use_container_width=True)
            image_metadata = get_image_social_metadata(owner_username, image_path.name)
            liked = viewer_username in image_metadata.get("liked_by", [])
            saved = viewer_username in image_metadata.get("saved_by", [])

            st.markdown(
                f"""
                <div class="post_footer">
                    <span>{len(image_metadata.get('liked_by', []))} likes</span>
                    <span>{len(image_metadata.get('saved_by', []))} saves</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            like_col, save_col = st.columns(2)
            with like_col:
                if st.button("Like" if not liked else "Liked", key=f"{key_prefix}_like_{owner_username}_{image_path.name}", use_container_width=True):
                    toggle_like(owner_username, image_path.name, viewer_username)
                    st.rerun()
            with save_col:
                if st.button("Save" if not saved else "Saved", key=f"{key_prefix}_save_{owner_username}_{image_path.name}", use_container_width=True):
                    toggle_save(owner_username, image_path.name, viewer_username)
                    st.rerun()
            if owner_username == viewer_username:
                confirm_delete = st.checkbox("Confirm delete", key=f"{key_prefix}_confirm_delete_{owner_username}_{image_path.name}")
                if st.button("Delete image", key=f"{key_prefix}_delete_{owner_username}_{image_path.name}", use_container_width=True, disabled=not confirm_delete):
                    if delete_note_image(owner_username, image_path.name):
                        st.rerun()

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


user_images = [(owner_username, image_path) for owner_username, image_path in iter_note_images() if owner_username == selected_user]
liked_images = get_user_social_images(selected_user, "liked")
saved_images = get_user_social_images(selected_user, "saved")
uploads_tab, liked_tab, saved_tab = st.tabs(["Uploads", "Liked", "Saved"])
with uploads_tab:
    st.markdown('<div class="section_title"><h2>Recent uploads</h2></div>', unsafe_allow_html=True)
    render_image_grid(user_images, "This user has not uploaded any notes yet.", "profile_uploads")
with liked_tab:
    st.markdown('<div class="section_title"><h2>Liked images</h2></div>', unsafe_allow_html=True)
    render_image_grid(liked_images, "No liked images yet.", "profile_liked")
with saved_tab:
    st.markdown('<div class="section_title"><h2>Saved images</h2></div>', unsafe_allow_html=True)
    render_image_grid(saved_images, "No saved images yet.", "profile_saved")

render_app_footer()
