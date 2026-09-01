import streamlit as st

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

col1, col2 = st.columns(2)

with col1:
    if st.button("Subjects", use_container_width=True):
        st.info("Subjects section opened.")

with col2:
    if st.button("PDF", use_container_width=True):
        st.info("PDF section opened.")


col3, col4 = st.columns(2)

with col3:
    if st.button("History", use_container_width=True):
        st.info("History section opened.")

with col4:
    if st.button("AI Summarize", use_container_width=True):
        st.info("AI Summarize section opened.")