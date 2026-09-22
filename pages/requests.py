import base64
import datetime
import html

import streamlit as st

from backend.admin import log_activity
from backend.auth import require_auth
from backend.requests import create_request, create_responses, list_requests, list_responses, list_user_note_files, response_file, save_uploaded_photo
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Requests", layout="wide", initial_sidebar_state="expanded")
require_auth()
render_sidebar("requests")

with open("styles/requests.css", encoding="utf-8") as file:
    page_css = file.read()
with open("images/backg.png", "rb") as file:
    background_image = base64.b64encode(file.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)

current_username = st.session_state.get("user_username", "member")

st.markdown(
    """
    <section class="requests_hero">
        <div>
            <span class="eyebrow">COMMUNITY REQUESTS</span>
            <h1>Ask for the missing piece.</h1>
            <p>Describe what you need, and let someone in the community send the right note your way.</p>
        </div>
        <div class="request_signal">
            <span>THE LOOP</span>
            <strong>Ask. Find. Share.</strong>
            <small>Good study communities move knowledge both ways.</small>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

open_requests = list_requests("open")
fulfilled_requests = list_requests("fulfilled")
metric_cols = st.columns(3)
with metric_cols[0]:
    st.markdown(f'<div class="request_metric"><span>OPEN REQUESTS</span><strong>{len(open_requests)}</strong><small>waiting for a helpful note</small></div>', unsafe_allow_html=True)
with metric_cols[1]:
    st.markdown(f'<div class="request_metric"><span>FULFILLED</span><strong>{len(fulfilled_requests)}</strong><small>requests answered by peers</small></div>', unsafe_allow_html=True)
with metric_cols[2]:
    st.markdown(f'<div class="request_metric"><span>YOUR NOTES</span><strong>{len(list_user_note_files(current_username))}</strong><small>ready to share</small></div>', unsafe_allow_html=True)

create_col, browse_col = st.columns([0.9, 1.6], gap="large")
with create_col:
    st.markdown('<div class="request_panel"><span class="section_kicker">MAKE AN ASK</span><h2>What are you looking for?</h2><p class="panel_hint">Be specific enough that someone can recognize the right file.</p>', unsafe_allow_html=True)
    with st.form("create_request_form", clear_on_submit=True):
        request_title = st.text_input("Request title", placeholder="e.g. Organic chemistry reaction map", label_visibility="collapsed")
        request_description = st.text_area("Request details", placeholder="Add a chapter, lecture, exam, or topic so people know what to send.", height=120, label_visibility="collapsed")
        request_category = st.selectbox("Category", ["General", "Mathematics", "Science", "Computer Science", "Languages", "History", "Business", "Exam Revision", "Projects"])
        request_submitted = st.form_submit_button("Post request", type="primary", use_container_width=True)
    if request_submitted:
        request_id = create_request(current_username, request_title, request_description, request_category)
        if request_id:
            log_activity(current_username, "create_request", str(request_id), request_category)
            st.success("Your request is live for the community.")
            st.rerun()
        else:
            st.error("Add a short title before posting your request.")
    st.markdown('</div>', unsafe_allow_html=True)

with browse_col:
    st.markdown('<div class="request_browse_head"><div><span class="section_kicker">THE COMMUNITY BOARD</span><h2>Open requests</h2></div><span class="board_count">Live now</span></div>', unsafe_allow_html=True)
    if not open_requests:
        st.info("No open requests right now. Your next question could start the board.")
    for request in open_requests:
        created_at = datetime.datetime.fromisoformat(request["created_at"]).astimezone().strftime("%b %d")
        is_owner = request["requester_username"] == current_username
        st.markdown(
            f'''
            <article class="request_row">
                <div class="request_avatar">{html.escape(request["requester_username"][:2].upper())}</div>
                <div class="request_copy">
                    <div class="request_row_top"><span class="request_category">{html.escape(request["category"])}</span><time>{created_at}</time></div>
                    <h3>{html.escape(request["title"])}</h3>
                    <p>{html.escape(request["description"] or "No extra details added.")}</p>
                    <small>Requested by @{html.escape(request["requester_username"])}</small>
                </div>
            </article>
            ''',
            unsafe_allow_html=True,
        )
        if not is_owner:
            note_files = list_user_note_files(current_username)
            with st.expander("Help with this request", expanded=False):
                with st.form(f"respond_form_{request['id']}"):
                    note_options = ["Upload a new photo"] + [item.name for item in note_files]
                    selected_note = st.selectbox(
                        "Choose an existing note",
                        note_options,
                        key=f"response_file_{request['id']}",
                    )
                    uploaded_photo = st.file_uploader(
                        "Or upload photos",
                        type=["png", "jpg", "jpeg", "gif", "bmp", "webp"],
                        key=f"response_photo_{request['id']}",
                        accept_multiple_files=True,
                        help="Share a photo of handwritten work, a whiteboard, or a useful page.",
                    )
                    response_message = st.text_input("Message", placeholder="Why is this useful for the request?", key=f"response_message_{request['id']}")
                    response_submitted = st.form_submit_button("Send help", type="primary", use_container_width=True)
                if response_submitted:
                    uploaded_photos = uploaded_photo or []
                    shared_paths = [save_uploaded_photo(current_username, photo) for photo in uploaded_photos]
                    if any(shared_path is None for shared_path in shared_paths):
                        st.error("Each uploaded photo must be a supported image under 50 MB.")
                    else:
                        shared_filenames = [shared_path.name for shared_path in shared_paths]
                        if not shared_filenames and selected_note != "Upload a new photo":
                            shared_filenames = [selected_note]
                        if not shared_filenames:
                            st.error("Choose an existing note or upload at least one photo first.")
                        elif create_responses(request["id"], current_username, shared_filenames, response_message):
                            log_activity(current_username, "fulfill_request", str(request["id"]), ", ".join(shared_filenames))
                            st.success(f"{len(shared_filenames)} note{'s' if len(shared_filenames) != 1 else ''} sent.")
                            st.rerun()
        responses = list_responses(request["id"])
        if responses:
            for response in responses:
                note_path = response_file(response)
                if note_path is None:
                    continue
                st.markdown(
                    f'<div class="response_row"><strong>Shared by @{html.escape(response["responder_username"])}</strong><span>{html.escape(response["message"] or "A community note for your request.")}</span></div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Download shared note",
                    data=note_path.read_bytes(),
                    file_name=note_path.name,
                    mime="application/octet-stream",
                    key=f"request_download_{response['id']}",
                    use_container_width=True,
                )

st.markdown('<div class="fulfilled_heading"><span class="section_kicker">RECENTLY ANSWERED</span><h2>Community follow-through</h2></div>', unsafe_allow_html=True)
if fulfilled_requests:
    fulfilled_items = "".join(
        f'<span class="fulfilled_item"><strong>{html.escape(item["title"])}</strong><small>answered for @{html.escape(item["requester_username"])}</small></span>'
        for item in fulfilled_requests[:6]
    )
    st.markdown(f'<div class="fulfilled_strip">{fulfilled_items}</div>', unsafe_allow_html=True)
else:
    st.caption("Answered requests will collect here as the board grows.")

render_app_footer()
