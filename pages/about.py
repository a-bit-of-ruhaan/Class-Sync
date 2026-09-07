import streamlit as st

st.set_page_config(
	page_title="About ClassSync",
	layout="wide",
)

with open("styles/about.css") as f:
	st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
