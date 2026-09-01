import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="classync",

)

st.title("ClassSync")
st.write("your personal class data management system")
st.sidebar.title("Navigation")
st.sidebar.write("Hi user! Welcome to ClassSync. Please use the navigation bar to explore the app.")

st.sidebar.markdown("---")
st.sidebar.button("try ai!")

st.sidebar.markdown("---")
st.sidebar.markdown("### navigation")


col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Assignments")
    st.write("View, submit, and track your assignments.")
    st.button("Go to Assignments", use_container_width=True)


    with col2:
        st.empty()

with col3:
    st.subheader("📅 Schedule")
    st.write("Check your class schedule and upcoming events.")
    st.button("Go to Schedule", use_container_width=True)