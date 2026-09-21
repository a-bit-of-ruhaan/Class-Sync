import base64
import html

import streamlit as st

from backend.auth import require_auth
from backend.fact import generate_random_facts
from backend.social import get_user_metrics, iter_note_images
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(
    page_title="Classync | Home",
    page_icon="images/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_auth()

user_name = st.session_state.get("user_name", "Classync member")
user_username = st.session_state.get("user_username", "member")
initials = "".join(part[0] for part in user_name.split()[:2]).upper() or "C"
metrics = get_user_metrics(user_username)
community_notes = list(iter_note_images())

with open("styles/home.css", encoding="utf-8") as file:
    page_css = file.read()
with open("images/backg.png", "rb") as file:
    background_image = base64.b64encode(file.read()).decode("ascii")
with open("images/logo.png", "rb") as file:
    logo_image = base64.b64encode(file.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)

render_sidebar("home")

st.markdown(
    f'''<section class="dashboard_topbar">
        <div class="brand_lockup">
            <img src="data:image/png;base64,{logo_image}" alt="Classync logo">
            <span>STUDENT WORKSPACE</span>
        </div>
        <div class="topbar_identity"><span class="status_pip"></span>Signed in as @{html.escape(user_username)}</div>
    </section>''',
    unsafe_allow_html=True,
)

st.markdown(
    f'''<section class="welcome_hero">
        <div class="welcome_copy">
            <span class="section_kicker">YOUR LEARNING DASHBOARD</span>
            <h1>Good to see you, {html.escape(user_name.split()[0])}.</h1>
            <p>Capture ideas, turn long readings into clarity, and learn alongside your community.</p>
        </div>
        <div class="hero_signal"><span>FOCUS MODE</span><strong>Build your next study streak.</strong></div>
    </section>''',
    unsafe_allow_html=True,
)

st.markdown('<div class="dashboard_section_heading"><div><span class="section_kicker">YOUR TOOLKIT</span><h2>Make study time count</h2></div><span class="section_hint">Start anywhere</span></div>', unsafe_allow_html=True)

tool_cols = st.columns(2, gap="large")
with tool_cols[0]:
    st.markdown(
        '''<article class="tool_card tool_card_primary">
            <div class="tool_icon">✦</div>
            <div><span class="card_label">SMART SUM</span><h3>Turn reading into direction.</h3>
            <p>Upload a PDF, DOCX, or text file and get a focused summary with an AI study companion.</p></div>
        </article>''',
        unsafe_allow_html=True,
    )
with tool_cols[1]:
    st.markdown(
        f'''<article class="tool_card tool_card_secondary">
            <div class="tool_icon">▦</div>
            <div><span class="card_label">NOTEBOOK</span><h3>Keep your knowledge visible.</h3>
            <p>Browse the community album, save useful notes, and build a visual archive of what you learn.</p></div>
            <div class="tool_metric"><strong>{metrics["uploaded_count"]}</strong><span>your uploads</span></div>
        </article>''',
        unsafe_allow_html=True,
    )

st.markdown('<div class="dashboard_section_heading compact"><div><span class="section_kicker">COMMUNITY PULSE</span><h2>A quick look around</h2></div></div>', unsafe_allow_html=True)

snapshot_cols = st.columns(3, gap="medium")
snapshot_data = (
    ("Your uploads", metrics["uploaded_count"], "notes shared"),
    ("Saved for later", metrics["saved_count"], "notes bookmarked"),
    ("Community notes", len(community_notes), "notes in the room"),
)
for column, (label, value, caption) in zip(snapshot_cols, snapshot_data):
    with column:
        st.markdown(f'<div class="snapshot_card"><span>{label}</span><strong>{value}</strong><small>{caption}</small></div>', unsafe_allow_html=True)

default_facts = [
    "Spaced repetition improves long-term recall by revisiting ideas at expanding intervals.",
    "Teaching a concept in your own words is one of the fastest ways to find gaps in understanding.",
    "A short walk can improve creative thinking and help your brain change context between tasks.",
    "Handwritten notes often encourage deeper processing than copying text word for word.",
]
if "home_facts" not in st.session_state:
    st.session_state.home_facts = default_facts

st.markdown('<section class="insight_panel"><div class="insight_heading"><div><span class="section_kicker">ONE USEFUL IDEA</span><h2>Study insight</h2><p>Small shifts compound into better learning.</p></div></div>', unsafe_allow_html=True)
if st.button("Refresh insight", icon=":material/refresh:", key="randomize_facts"):
    try:
        with st.spinner("Finding a fresh insight..."):
            st.session_state.home_facts = generate_random_facts()
    except Exception:
        st.warning("The insight service is taking a moment. Showing your current ideas instead.")

safe_fact = html.escape(str(st.session_state.home_facts[0]))
st.markdown(f'<div class="featured_insight"><span class="insight_number">01</span><p>{safe_fact}</p><span class="insight_mark">+</span></div></section>', unsafe_allow_html=True)

st.markdown('<div class="dashboard_footer_note">Classync is your focused corner of the internet for learning together.</div>', unsafe_allow_html=True)
render_app_footer()
