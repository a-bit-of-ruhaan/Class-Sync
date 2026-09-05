import streamlit as st

st.markdown("""
<style>
 .stApp{
  background: linear-gradient(
        135deg,
        #051F20 0%,
        #0B2826 25%,
        #163B32 50%,
        #235347 75%,
        #051F20 100%
    );
    background-attachment: fixed;
    color: #DAF1DE;
}

/* Main title */
.my-title {
    color: #DAF1DE;
    font-size: 42px;
    font-weight: 700;
}

/* Custom box */
.my-box {
    background: linear-gradient(
        135deg,
        #163B32,
        #235347
    );
    border: 1px solid #8EB69B;
    border-radius: 15px;
    padding: 20px;
    color: #DAF1DE;
    box-shadow: 0 8px 25px rgba(5, 31, 32, 0.5);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #051F20,
        #0B2826,
        #163B32
    );
}

/* Buttons */
.stButton > button {
    background: linear-gradient(
        135deg,
        #235347,
        #163B32
    );
    color: #DAF1DE;
    border: 1px solid #8EB69B;
    border-radius: 10px;
    transition: 0.3s;
}

/* Button hover */
.stButton > button:hover {
    background: linear-gradient(
        135deg,
        #8EB69B,
        #235347
    );
    color: #051F20;
    border-color: #DAF1DE;
}

/* Search box / text inputs */
.stTextInput input {
    background-color: #0B2826;
    color: #DAF1DE;
    border: 1px solid #8EB69B;
    border-radius: 10px;
}

/* Headings and text */
h1, h2, h3, p, label {
    color: #DAF1DE !important;
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="ClassSync",
    layout="wide"
)

st.title("ClassSync")

with st.sidebar:
    st.header("Menu Bar")

    if st.button("Home"):
        st.write("Home")

    if st.button("Subjects"):
        st.write("Subjects")

    if st.button("PDF"):
        st.write("PDF")

    if st.button("History"):
        st.write("History")

    if st.button("AI Summarize"):
        st.write("AI Summarize")

    if st.button("Settings"):
        st.write("Settings")


search = st.text_input(
    "Search",
    placeholder="Search your subjects, PDFs, notes..."
)

st.write("")

col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("Subjects", use_container_width=True):
        st.info("Subjects section opened.")

with col2:
    if st.button("PDF", use_container_width=True):
        st.info("PDF section opened.")


col3, col4 = st.columns(2, gap="large")

with col3:
    if st.button("History", use_container_width=True):
        st.info("History section opened.")

with col4:
    if st.button("AI Summarize", use_container_width=True):
        st.info("AI Summarize section opened.")

st.markdown(
    '<div class="custom-divider"></div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">Your Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown("<div style='height:70px'></div>", unsafe_allow_html=True)

left, top, right = st.columns([0.7, 2.6, 0.7])

with top:
    st.markdown(
        '<div class="my-box" style="height:140px;"></div>',
        unsafe_allow_html=True
    )

st.markdown("<div style='height:35px'></div>", unsafe_allow_html=True)

left, box1, gap, box2, right = st.columns(
    [0.3, 1.3, 0.15, 1.3, 0.3]
)

with box1:
    st.markdown(
        '<div class="my-box" style="height:140px;"></div>',
        unsafe_allow_html=True
    )

with box2:
    st.markdown(
        '<div class="my-box" style="height:140px;"></div>',
        unsafe_allow_html=True
    )