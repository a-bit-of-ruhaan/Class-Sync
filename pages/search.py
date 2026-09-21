import base64
import html

import streamlit as st

from backend.auth import require_auth, search_user_profiles
from backend.social import get_profile_photo_data_uri, get_profile_photo_path, get_user_metrics
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Search Classync", layout="wide", initial_sidebar_state="expanded")
require_auth()
render_sidebar("search")

with open("styles/search.css", encoding="utf-8") as file:
    page_css = file.read()
with open("images/backg.png", "rb") as file:
    background_image = base64.b64encode(file.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)


def initials(value):
    return "".join(part[0].upper() for part in value.split()[:2]) or "C"


st.markdown(
    """
    <section class="search_header">
        <span class="eyebrow">FIND YOUR PEOPLE</span>
        <h1>Search Classync</h1>
        <p>Find learners by name, username, or what they are studying.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

query = st.text_input("Search users", placeholder="Try a name, @username, or study topic", label_visibility="collapsed")
if query.strip():
    results = search_user_profiles(query)
    st.markdown(f'<div class="search_result_count">{len(results)} people found</div>', unsafe_allow_html=True)
    if not results:
        st.info("No discoverable users matched that search.")
    else:
        for user in results:
            photo = get_profile_photo_path(user["username"])
            if photo:
                avatar = f'<img class="search_avatar" src="{get_profile_photo_data_uri(user["username"])}" alt="{html.escape(user["name"])}" />'
            else:
                avatar = f'<div class="search_avatar search_avatar_placeholder">{html.escape(initials(user["name"]))}</div>'
            metrics = get_user_metrics(user["username"])
            st.markdown(
                f'<div class="search_person"><div class="search_identity">{avatar}<div><strong>{html.escape(user["name"])}</strong><span>@{html.escape(user["username"])}</span><p>{html.escape(user.get("bio", "") or "Learning with Classync")}</p></div></div><div class="search_stats"><span>{metrics["uploaded_count"]} uploads</span><span>{metrics["liked_count"]} likes</span></div></div>',
                unsafe_allow_html=True,
            )
            if st.button(f'View {user["name"]} profile', key=f'search_profile_{user["username"]}', use_container_width=True):
                st.session_state["profile_username"] = user["username"]
                st.switch_page("pages/profile.py")
else:
    st.markdown('<div class="search_empty"><h2>Search the Classync community</h2><p>Profiles become easier to find when people add a bio or study interests.</p></div>', unsafe_allow_html=True)

render_app_footer()