import base64

import streamlit as st
import html
from backend.auth import require_auth
from backend.ai_api import summarizer_text

from backend.note_summarizer import extract_text_from_pdf, extract_text_from_docx

st.set_page_config(
    page_title="Summarizer",
    layout="wide"
)

require_auth()

with open("styles/summarizer.css", encoding="utf-8") as f:
    page_css = f.read()
with open("images/backg.png", "rb") as f:
    background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
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
            try:
                extracted_content = extract_document(uploaded_file)
            except Exception as error:
                st.error(f"We could not read that file: {error}")
                extracted_content = ""
        st.session_state.extracted_text = extracted_content
        st.session_state.file_name = uploaded_file.name
        if st.session_state.get("active_file_name") != uploaded_file.name:
            st.session_state.active_file_name = uploaded_file.name
            st.session_state.pop("summary", None)
            st.session_state.chat_history = []

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
    st.markdown(
        '<div><h2>SMART SUM</h2></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="chat_box">', unsafe_allow_html=True)

    # --------------------------------------------------
    # No document uploaded
    # --------------------------------------------------

    if "extracted_text" not in st.session_state:

        st.chat_message("assistant").markdown(
            """
            Hello! I'm **SMART SUM**.

            Upload a document on the left and I can:

            - Summarize the document
            - Answer questions about it
            - Explain difficult topics
            - Find important information
            """
        )

    # --------------------------------------------------
    # Document uploaded
    # --------------------------------------------------

    else:

        # Generate summary button
        if st.button(
            "Generate Summary",
            use_container_width=True
        ):

            with st.spinner("Analyzing your document..."):

                try:
                    summary = summarizer_text(
                        text="""
                    Summarize the uploaded document.

                    Include:
                    - A brief overview
                    - Main topics
                    - Important points
                    - Important facts, dates and numbers
                    - Main conclusions

                    Only use information from the uploaded document.
                    """,

                        document_text=st.session_state.extracted_text,
                        conversation_history="",
                    )
                except Exception as error:
                    st.error(f"Smart Sum could not generate a summary: {error}")
                else:
                    st.session_state.summary = summary


        # --------------------------------------------------
        # Show summary if generated
        # --------------------------------------------------

        if "summary" in st.session_state:

            with st.chat_message("assistant"):

                st.markdown(
                    st.session_state.summary
                )

        for message in st.session_state.get("chat_history", []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


        # --------------------------------------------------
        # Chat input
        # --------------------------------------------------

        user_question = st.chat_input(
            "Ask something about your document..."
        )


        if user_question:

            history = "\n".join(
                f"{message['role'].title()}: {message['content']}"
                for message in st.session_state.get("chat_history", [])
            )
            with st.spinner("Thinking..."):
                try:
                    answer = summarizer_text(
                        text=user_question,
                        document_text=st.session_state.extracted_text,
                        conversation_history=history,
                    )
                except Exception as error:
                    st.error(f"Smart Sum could not answer that: {error}")
                else:
                    st.session_state.setdefault("chat_history", []).extend(
                        [{"role": "user", "content": user_question}, {"role": "assistant", "content": answer}]
                    )
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)