import streamlit as st

st.title("Feedback Form")
st.write("Please fill out the form below to provide your feedback.")

with st.form("form_id"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Name")
        email = st.text_input("Email")

    with col2:
        phone_number = st.text_input("Phone Number")
        Gender = st.radio("Select your Gender", ("Male", "Female", "Other"))
        st.write(f"You Selected: {Gender}")

    feedback = st.text_area("Your Feedback", max_chars=200)

    submitted = st.form_submit_button("Submit Feedback")

if submitted:
    if name and email and feedback:
        st.success(f"Thanks {name}! Your feedback has been received.")
    else:
        st.warning("⚠️Please fill in all required fields (Name, Email, and Feedback).")
