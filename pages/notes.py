import base64

import streamlit as st
import pathlib as path
import os

from backend.auth import require_auth


st.set_page_config(
    page_title="NOTES",
    layout="wide"
)

require_auth()

with open("styles/notes.css") as f:
    page_css = f.read()
with open("images/backg.png", "rb") as f:
    background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)

st.markdown("""<div class="header_main">
                <h1>Find Your Notes</h1>
                <p>Get useful notes or upload your own</p>
            </div>""", unsafe_allow_html=True)

col_upload,  col_find = st.columns([1, 2])

with col_upload:
    st.subheader("Upload Your Notes")
    uploaded_file = st.file_uploader("Choose a file", type=["image"], key="image_uploader")
    if uploaded_file is not None:
        # Save the uploaded file to the 'notes' directory
        notes_dir = path.Path("notes")
        notes_dir.mkdir(exist_ok=True)
        file_path = notes_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")

 

with col_find:
    col_finder, col_img = st.columns([2,1])

    with col_finder:
        st.subheader("Find Your Notes")
        notes_dir = path.Path("notes")
        if notes_dir.exists():
            note_files = [f.name for f in notes_dir.iterdir() if f.is_file()]
            if note_files:
                selected_note = st.selectbox("Select a note to view", note_files)
                file_path = notes_dir / selected_note
            else:
                selected_note = None
        else:
            note_files = []
            selected_note = None

    with col_img:
        if selected_note:
            st.image(file_path, caption=selected_note, width=300)
        else:
            st.info("No notes found. Please upload your notes first.")

st.markdown('<div class="image_grid">', unsafe_allow_html=True)
st.markdown('<h2>Recently Uploaded Notes</h2>', unsafe_allow_html=True)

# Display uploaded images in a 4-column grid
notes_dir = path.Path("notes")
if notes_dir.exists():
    image_files = [f for f in notes_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']]
    
    if image_files:
        # Sort by modification time (newest first)
        image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Create grid with 4 columns
        cols_per_row = 5
        for i in range(0, len(image_files), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, col in enumerate(cols):
                img_idx = i + col_idx
                if img_idx < len(image_files):
                    with col:
                        st.image(str(image_files[img_idx]), caption=image_files[img_idx].name, use_container_width=True)
    else:
        st.info("No images uploaded yet.")
else:
    st.info("Notes directory not found.")

st.markdown('</div>', unsafe_allow_html=True)