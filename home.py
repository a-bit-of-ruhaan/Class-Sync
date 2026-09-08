import base64
import html

from anyio import Path

import streamlit as st

from backend.fact import generate_random_facts


st.set_page_config(
    layout="wide",
    page_title="classync",
    initial_sidebar_state="collapsed"

)

# injecting css
with open("styles/home.css") as f:
    page_css = f.read()
with open("images/backg.png", "rb") as f:
    background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)

#header of the page

st.markdown("""<div class="header_main">
                <h1>Welcome to Classync</h1>
                <p>Your AI-powered study companion</p>
            </div>""", unsafe_allow_html=True)

#sidebar configuration


#main content

col1, col2, col3= st.columns([2,1,2 ])

with col1:

    col_text, col_img = st.columns([2,2])
    with col_text:
     st.subheader("Summarizer")
    
     st.write("Get your pdf, docx and other txt files summarized with our Smart Sum AI")
     if st.button("Get Summary of Your Files", use_container_width=True):
      st.switch_page("pages/summarizer.py")

    with col_img:
     st.image("images/summarize.png", width=400)

with col2:
   st.empty()

with col3:

    col_text, col_img = st.columns([2,2])
    with col_text:
     st.subheader("View Notes")
   
     st.write("Keep track of your previous notes and don't miss any.")
     if st.button("View Notes", use_container_width=True):
       st.switch_page("pages/notes.py")
    with col_img:
     st.image("images/note.png", width=400)   



st.markdown('<div class="content_container">', unsafe_allow_html=True)
st.markdown('<div class="content_box">', unsafe_allow_html=True)
st.markdown('<h2>DID YOU KNOW?</h2>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Random fact box
default_facts = [
    "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs.",
    "Octopuses have three hearts, and two of them stop beating when the animal swims.",
    "A day on Venus is longer than a year on Venus because it rotates very slowly.",
    "Bananas are berries, while strawberries are technically aggregate fruits.",
]

if "home_facts" not in st.session_state:
    st.session_state.home_facts = default_facts

st.markdown(
    '<div class="fact_box"><div class="fact_header">'
    '<div><span class="fact_kicker">CURIOUS MINDS</span>'
    '<h3>Did you know?</h3>'
    '<p>Fresh sparks of knowledge, one row at a time.</p></div>',
    unsafe_allow_html=True,
)

if st.button("Randomize facts", use_container_width=True, key="randomize_facts"):
    try:
        with st.spinner("Finding four fresh facts..."):
            new_facts = generate_random_facts()
        st.session_state.home_facts = new_facts
    except Exception as error:
        st.warning("The fact service is taking a moment. Showing the current facts instead.")
        st.caption(f"Error: {error}")

st.markdown('</div><div class="fact_list">', unsafe_allow_html=True)

for index, fact in enumerate(st.session_state.home_facts, start=1):
    safe_fact = html.escape(str(fact))
    st.markdown(
        f'<div class="fact_item"><span class="fact_index">0{index}</span>'
        f'<p>{safe_fact}</p><span class="fact_arrow">+</span></div>',
        unsafe_allow_html=True,
    )

st.markdown('</div></div>', unsafe_allow_html=True)

