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

st.markdown('<div class="content_container">', unsafe_allow_html=True)
st.markdown('<div class="content_box">', unsafe_allow_html=True)
st.markdown('<h4>About ClassSync</h4>', unsafe_allow_html=True)
st.markdown('<p>ClassSync is a comprehensive platform designed to help students manage their class data effectively. With features like note uploading, viewing, and summarization, ClassSync aims to streamline the learning process and enhance productivity.</p>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


st.markdown('<div class="recents_container">', unsafe_allow_html=True)


col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Summarizer")
    st.write("Get your pdf, docx and other txt files summarized with our Smart Sum AI")
    if st.button("Get Summary of Your Files", use_container_width=True):
     st.switch_page("pages/summarizer.py")


    with col2:
        st.empty()

with col3:
    st.subheader("View Notes")
    st.write("Keep track of your previous notes and don't miss any.")
    if st.button("View Notes", use_container_width=True):
      st.switch_page("pages/notes.py")



st.markdown('<div class="content_container">', unsafe_allow_html=True)
st.markdown('<div class="content_box">', unsafe_allow_html=True)
st.markdown('<h2>DID YOU KNOW?</h2>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)



