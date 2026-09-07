import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="classync",
    initial_sidebar_state="collapsed"

)

#injecting css

with open("styles/home.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#header of the page

st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>ClassSync</h1>', unsafe_allow_html=True)
st.markdown('<p>Welcome to ClassSync, your ultimate study companion!</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

#sidebar configuration


#main content

col1, col2, col3= st.columns([1,2,1])

with col1:
    st.subheader("Summarizer")
    st.image("images/summarize.png", width=200)
    st.write("Get your pdf, docx and other txt files summarized with our Smart Sum AI")
    if st.button("Get Summary of Your Files", use_container_width=True):
     st.switch_page("pages/summarizer.py")

with col2:
   st.empty()

with col3:
    st.subheader("View Notes")
    st.image("images/note.png", width=200)
    st.write("Keep track of your previous notes and don't miss any.")
    if st.button("View Notes", use_container_width=True):
      st.switch_page("pages/notes.py")



st.markdown('<div class="content_container">', unsafe_allow_html=True)
st.markdown('<div class="content_box">', unsafe_allow_html=True)
st.markdown('<h2>DID YOU KNOW?</h2>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


