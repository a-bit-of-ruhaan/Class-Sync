import base64

import streamlit as st

from backend.auth import authenticate_user, log_in, register_user


st.set_page_config(
    page_title="Enter Classync",
    page_icon="images/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if st.session_state.get("authenticated", False):
    st.switch_page("home.py")

with open("styles/login.css", encoding="utf-8") as file:
    page_css = file.read()
with open("images/backg.png", "rb") as file:
    background_image = base64.b64encode(file.read()).decode("ascii")
with open("images/logo.png", "rb") as file:
    logo_image = base64.b64encode(file.read()).decode("ascii")

st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)

intro_column, panel_column = st.columns([1.05, 0.8], gap="small")

with intro_column:
    st.markdown(
        f"""<section class="login_intro">
            <img class="login_logo" src="data:image/png;base64,{logo_image}" alt="ClassSync logo">
            <div>
                <span class="login_eyebrow">A CALMER WAY TO LEARN</span>
                <h1>Your ideas deserve a place to grow.</h1>
                <p>Bring your notes, summaries, and sparks of curiosity into one focused learning space.</p>
            </div>
            <span class="login_note">Classync · learn smarter, together.</span>
        </section>""",
        unsafe_allow_html=True,
    )

with panel_column:
    st.markdown(
        """<section class="login_panel">
            <h2>Welcome back</h2>
            <p>Sign in to continue your learning journey.</p>
            <span class="login_panel_anchor"></span>
        </section>""",
        unsafe_allow_html=True,
    )
    mode = st.radio(
        "Account access",
        ["Log in", "Create account"],
        horizontal=True,
        label_visibility="collapsed",
    )
    with st.form("auth_form"):
        name = ""
        username = ""
        if mode == "Create account":
            name = st.text_input("Your name", placeholder="e.g. Alex Morgan")
            username = st.text_input("Username", placeholder="e.g. alex_morgan")
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="At least 8 characters")
        confirm_password = ""
        if mode == "Create account":
            confirm_password = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button(
            "Enter Classync" if mode == "Log in" else "Create my account",
            use_container_width=True,
        )

    if submitted:
        if mode == "Log in":
            if authenticate_user(email, password):
                log_in(email)
                st.switch_page("home.py")
            else:
                st.error("That email and password combination could not be verified.")
        elif password != confirm_password:
            st.error("Your passwords do not match.")
        else:
            created, message = register_user(name, username, email, password)
            if created:
                log_in(email)
                st.switch_page("home.py")
            else:
                st.error(message)
