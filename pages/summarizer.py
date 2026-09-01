import streamlit as st
import pathlib as path
import html
from backend.ai_api import summarizer_text

from backend.note_summarizer import extract_text_from_pdf, extract_text_from_docx

st.set_page_config(
    page_title="Summarizer",
    layout="wide"
)

#title and info about classSync
st.markdown('<h1>Summarize Your Notes</h1>', unsafe_allow_html=True)
st.markdown("""<p>Welcome to the Class Sync Summarizer! This tool allows you to input text and receive a concise summary of the content.
 Simply paste your text into the input box below and click "Summarize" to get started.</p>""", unsafe_allow_html=True)

#main columns of the page, left for uploading and right for conversation
col_left, col_mid, col_right = st.columns([2,1,2])

#there we can upoad pdf,docx and txt file to extract its content
with col_left:

    def extract_document(uploaded_file):
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name.lower()
        if filename.endswith(".pdf"):
            return extract_text_from_pdf(file_bytes)
        if filename.endswith(".docx"):
            return extract_text_from_docx(file_bytes)
        return file_bytes.decode("utf-8", errors="ignore")

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )

    if uploaded_file is None:
        st.markdown(
            """
            <div class="empty-upload">
                <div class="upload-docs">↥</div>
                <strong>Drop your reading here</strong>
                <span>Text Extractor</span>
            </div>
            """,
            unsafe_allow_html=True,)
    else:
        with st.spinner("Reading your document..."):
            extracted_content = extract_document(uploaded_file)
        st.session_state.extracted_text = extracted_content
        st.session_state.file_name = uploaded_file.name

        safe_name = html.escape(uploaded_file.name)
        word_count = len(extracted_content.split())
        st.markdown(
            f"""
            <div class="file-status">
                <div class="file-status-top"><span class="status-dot"></span> READY TO READ</div>
                <div class="file-name">{safe_name}</div>
                <div class="file-stats"><span>{word_count:,} words</span><span>{uploaded_file.size / 1024:.1f} KB</span><span>Text extracted</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Preview extracted text"):
            st.text(extracted_content[:3000] or "No readable text was found in this file.")

    st.markdown(
        '<div class="tip-line"><span>✦</span> Upload first, then use the conversation to explore the document.</div>',
        unsafe_allow_html=True,
    )

with col_mid:
    st.empty()

#there we will get the summarized version of the uploaded document and also we can ask questions about the document
with col_right:
    st.markdown('<div><h2>Summarizer</h2></div>', unsafe_allow_html=True)
    st.markdown('<div class="chat_box">', unsafe_allow_html=True)
    if "extracted_text" not in st.session_state:
        st.chat_message("user").markdown("Hello! I'm here to help you summarize your document. Please provide the text you'd like me to summarize.")
     