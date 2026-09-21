import base64
import html
import mimetypes

import streamlit as st

from backend.social import get_profile_photo_path


def _initials(value: str) -> str:
    parts = [part for part in value.split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "C"


def _avatar_markup(username: str, name: str) -> str:
    photo_path = get_profile_photo_path(username)
    if photo_path:
        mime_type = mimetypes.guess_type(photo_path.name)[0] or "image/png"
        image_data = base64.b64encode(photo_path.read_bytes()).decode("ascii")
        return f'<img class="sidebar_avatar" src="data:{mime_type};base64,{image_data}" alt="{html.escape(name)}" />'
    return f'<div class="sidebar_avatar sidebar_avatar_placeholder">{html.escape(_initials(name))}</div>'


def _inject_shell_styles() -> None:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { background: rgba(8, 11, 19, 0.94) !important; border-right: 1px solid rgba(255,255,255,0.08); }
        [data-testid="stSidebarNav"] { display: none !important; }
        .sidebar_identity { display: flex; align-items: center; gap: 0.75rem; padding: 0.8rem; border: 1px solid rgba(125,211,252,0.2); border-radius: 14px; background: linear-gradient(135deg, rgba(45,212,191,0.14), rgba(59,130,246,0.12)); }
        .sidebar_avatar { width: 2.65rem; height: 2.65rem; flex: 0 0 2.65rem; border-radius: 50%; object-fit: cover; display: grid; place-items: center; background: linear-gradient(135deg, #67e8f9, #60a5fa); color: #081521; font-weight: 800; }
        .sidebar_avatar_placeholder { font-size: 0.9rem; }
        .sidebar_identity_text { min-width: 0; display: flex; flex-direction: column; }
        .sidebar_identity_text strong, .sidebar_identity_text small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .sidebar_identity_text strong { color: #eff6ff; font-size: 0.95rem; }
        .sidebar_identity_text small { color: rgba(233,239,255,0.62); font-size: 0.76rem; }
        .sidebar_label { margin: 1.25rem 0 0.45rem; color: #7dd3fc; font-size: 0.65rem; font-weight: 800; letter-spacing: 0.16em; }
        .sidebar_rule { height: 1px; margin: 1rem 0; background: rgba(148,163,184,0.16); }
        section[data-testid="stSidebar"] .stButton > button { min-height: 2.45rem; justify-content: flex-start; border: 1px solid transparent !important; background: transparent !important; color: #dbeafe !important; font-weight: 600 !important; }
        section[data-testid="stSidebar"] .stButton > button:hover { border-color: rgba(125,211,252,0.2) !important; background: rgba(125,211,252,0.08) !important; }
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: rgba(233,239,255,0.55); }
        .app_footer { display: flex; justify-content: space-between; gap: 1rem; align-items: center; margin-top: 3rem; padding: 1.15rem 0 0.5rem; border-top: 1px solid rgba(148,163,184,0.16); color: rgba(233,239,255,0.56); font-size: 0.78rem; }
        .app_footer_brand { color: #8fe1d3; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
        .app_footer_meta { text-align: right; }
        @media (max-width: 640px) { .app_footer { align-items: flex-start; flex-direction: column; } .app_footer_meta { text-align: left; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(key_prefix: str) -> None:
    from backend.auth import log_out
    from backend.admin import is_admin
    from backend.chat import get_unread_count

    _inject_shell_styles()
    user_name = st.session_state.get("user_name", "Classync member")
    username = st.session_state.get("user_username", "member")
    with st.sidebar:
        st.markdown(
            f'<div class="sidebar_identity">{_avatar_markup(username, user_name)}'
            f'<div class="sidebar_identity_text"><strong>{html.escape(user_name)}</strong>'
            f'<small>@{html.escape(username)}</small></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar_label">WORKSPACE</div>', unsafe_allow_html=True)
        unread_count = get_unread_count(username)
        chat_label = f"Chat ({unread_count})" if unread_count else "Chat"
        nav_items = (
            ("Home", "home", "home.py"),
            ("Notes", "edit_note", "pages/notes.py"),
            ("Summarize", "auto_awesome", "pages/summarizer.py"),
            ("Explore", "explore", "pages/explore.py"),
            ("Search", "search", "pages/search.py"),
            ("Games", "sports_esports", "pages/games.py"),
            ("Profile", "person", "pages/profile.py"),
            (chat_label, "chat", "pages/chat.py"),
        )
        if is_admin(st.session_state.get("user_email", "")):
            nav_items += (("Developer", "admin_panel_settings", "pages/admin.py"),)
        for label, icon, page in nav_items:
            if st.button(label, key=f"sidebar_{key_prefix}_{icon}", use_container_width=True, icon=f":material/{icon}:"):
                if label == "Profile":
                    st.session_state["profile_username"] = username
                st.switch_page(page)
        st.markdown('<div class="sidebar_rule"></div>', unsafe_allow_html=True)
        st.caption("Your focused corner of the internet for learning together.")
        if st.button("Log out", key=f"sidebar_{key_prefix}_logout", use_container_width=True, icon=":material/logout:"):
            log_out()
            st.switch_page("pages/login.py")


def render_app_footer() -> None:
    username = html.escape(st.session_state.get("user_username", "member"))
    st.markdown(
        f'<footer class="app_footer"><span class="app_footer_brand">Classync</span>'
        f'<span class="app_footer_meta">Made for focused learning - Signed in as @{username}</span></footer>',
        unsafe_allow_html=True,
    )
