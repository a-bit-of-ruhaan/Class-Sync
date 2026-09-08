import base64

import streamlit as st

st.set_page_config(
	page_title="About ClassSync",
	layout="wide",
)

with open("styles/about.css") as f:
	page_css = f.read()
with open("images/backg.png", "rb") as f:
	background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
	f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
	unsafe_allow_html=True,
)
