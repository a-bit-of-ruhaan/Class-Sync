import streamlit as st

st.set_page_config(
    page_title="ClassSync",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>

    /* ---------- MAIN PAGE ---------- */

    .stApp {
        background: #ffffff;
    }

    .main .block-container {
        max-width: 1100px;
        padding-top: 35px;
        padding-left: 55px;
        padding-right: 55px;
        padding-bottom: 50px;
    }


    /* ---------- TITLE ---------- */

    .class-title {
        font-size: 30px;
        font-weight: 400;
        color: #111111;
        margin-bottom: 115px;
        margin-left: 0px;
    }


    /* ---------- TOP BUTTONS ---------- */

    .top-grid {
        margin-bottom: 50px;
    }

    .top-button button {
        height: 65px !important;
        border-radius: 10px !important;

        background: #4775C4 !important;
        color: transparent !important;

        border: 1px solid #315A9E !important;

        box-shadow: none !important;
    }

    .top-button button:hover {
        background: #3F6DB8 !important;
        border: 1px solid #315A9E !important;
        color: transparent !important;
    }


    /* ---------- DASHBOARD TITLE ---------- */

    .dashboard-title {
        font-size: 26px;
        font-weight: 400;
        color: #111111;
        margin-top: 5px;
        margin-bottom: 35px;
    }


    /* ---------- CENTER CARD ---------- */

    .center-card {
        height: 100px;

        background: #4775C4;

        border: 1px solid #315A9E;
        border-radius: 16px;

        margin: 0 auto;

        box-shadow: none;
    }


    /* ---------- BOTTOM CARDS ---------- */

    .bottom-card {
        height: 90px;

        background: #4775C4;

        border: 1px solid #315A9E;
        border-radius: 16px;

        box-shadow: none;
    }


    /* ---------- REMOVE STREAMLIT EXTRA SPACING ---------- */

    div[data-testid="column"] {
        padding-left: 10px;
        padding-right: 10px;
    }

    div[data-testid="stButton"] {
        margin: 0px !important;
    }

</style>
""", unsafe_allow_html=True)


st.markdown(
    '<div class="class-title">CLASS SYNC</div>',
    unsafe_allow_html=True
)

top1, top2 = st.columns(2, gap="medium")

with top1:
    st.markdown('<div class="top-button">', unsafe_allow_html=True)
    st.button(
        "Subjects",
        key="subjects",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with top2:
    st.markdown('<div class="top-button">', unsafe_allow_html=True)
    st.button(
        "PDF",
        key="pdf",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


top3, top4 = st.columns(2, gap="medium")

with top3:
    st.markdown('<div class="top-button">', unsafe_allow_html=True)
    st.button(
        "History",
        key="history",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with top4:
    st.markdown('<div class="top-button">', unsafe_allow_html=True)
    st.button(
        "AI Summarize",
        key="ai_summarize",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="dashboard-title">dashboard</div>',
    unsafe_allow_html=True
)


left, center, right = st.columns(
    [1, 2, 1],
    gap="medium"
)

with center:
    st.markdown(
        '<div class="center-card"></div>',
        unsafe_allow_html=True
    )


st.markdown("<div style='height:45px'></div>", unsafe_allow_html=True)


left, bottom1, bottom2, right = st.columns(
    [0.15, 1, 1, 0.15],
    gap="large"
)

with bottom1:
    st.markdown(
        '<div class="bottom-card"></div>',
        unsafe_allow_html=True
    )

with bottom2:
    st.markdown(
        '<div class="bottom-card"></div>',
        unsafe_allow_html=True
    )
