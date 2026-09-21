import base64
import html

import streamlit as st

from backend.admin import delete_user_note, is_admin, list_activity, list_users, set_user_banned, user_notes
from backend.auth import require_auth
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Developer Console", layout="wide", initial_sidebar_state="expanded")
require_auth()

if not is_admin(st.session_state.get("user_email", "")):
    st.error("Developer access is required for this page.")
    st.stop()

render_sidebar("admin")

with open("images/backg.png", "rb") as file:
    background_image = base64.b64encode(file.read()).decode("ascii")
st.markdown(
    f"""<style>
    .stApp {{ background: radial-gradient(circle at top right, rgba(239,68,68,0.12), transparent 28%), linear-gradient(135deg,#0b1220,#101827); color:#edf6ff; }}
    .admin_header {{ padding: 2rem 0 1.5rem; }}
    .admin_header h1 {{ margin: .3rem 0; font-family: 'Space Grotesk', sans-serif; }}
    .admin_card {{ padding: 1rem; margin: .6rem 0; border: 1px solid rgba(148,163,184,.15); border-radius: 12px; background: rgba(15,23,42,.65); }}
    .activity_line {{ color: rgba(233,239,255,.75); font-size: .88rem; }}
    </style>""",
    unsafe_allow_html=True,
)

admin_username = st.session_state.get("user_username", "developer")
st.markdown('<section class="admin_header"><span class="eyebrow">PRIVATE DEVELOPER AREA</span><h1>Moderation Console</h1><p>Review activity, control accounts, and remove content that violates community rules.</p></section>', unsafe_allow_html=True)

users_tab, content_tab, activity_tab = st.tabs(["Users", "Uploaded notes", "Activity log"])
with users_tab:
    users = list_users()
    st.metric("Registered users", len(users))
    for user in users:
        user_col, action_col = st.columns([3, 1])
        with user_col:
            status = "Banned" if user["banned"] else "Active"
            st.markdown(f'<div class="admin_card"><strong>{html.escape(user["name"])}</strong> @{html.escape(user["username"])}<br><small>{html.escape(user["email"])} · {status}</small></div>', unsafe_allow_html=True)
        with action_col:
            if user["username"] == admin_username:
                st.caption("Current developer")
            elif st.button("Unban" if user["banned"] else "Ban", key=f"admin_ban_{user['username']}", use_container_width=True):
                set_user_banned(user["username"], not bool(user["banned"]), admin_username)
                st.rerun()

with content_tab:
    notes = user_notes()
    if not notes:
        st.info("No uploaded notes found.")
    for owner, filename, _ in notes:
        note_col, delete_col = st.columns([3, 1])
        with note_col:
            st.markdown(f'<div class="admin_card"><strong>{html.escape(filename)}</strong><br><small>Uploaded by @{html.escape(owner)}</small></div>', unsafe_allow_html=True)
        with delete_col:
            confirm = st.checkbox("Confirm", key=f"admin_confirm_{owner}_{filename}")
            if st.button("Delete", key=f"admin_delete_{owner}_{filename}", disabled=not confirm, use_container_width=True):
                delete_user_note(owner, filename, admin_username)
                st.rerun()

with activity_tab:
    activities = list_activity()
    if not activities:
        st.info("No moderation activity has been recorded yet.")
    for activity in activities:
        st.markdown(f'<div class="activity_line"><strong>{html.escape(activity["action"])}</strong> by @{html.escape(activity["username"])} · {html.escape(activity["target"])} · {html.escape(activity["created_at"])}</div>', unsafe_allow_html=True)

render_app_footer()