import base64
import datetime
import html

import streamlit as st

from backend.auth import require_auth
from backend.chat import (
    block_user,
    create_direct_conversation,
    create_group_conversation,
    get_messages,
    is_user_online,
    list_chat_users,
    list_conversations,
    list_mates,
    list_shareable_notes,
    mark_conversation_read,
    report_user,
    send_message,
    touch_presence,
)
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Chat", layout="wide", initial_sidebar_state="expanded")
require_auth()
render_sidebar("chat")

with open("styles/chat.css", encoding="utf-8") as file:
    page_css = file.read()
with open("images/backg.png", "rb") as file:
    background_image = base64.b64encode(file.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)


def format_time(value: str) -> str:
    timestamp = datetime.datetime.fromisoformat(value)
    return timestamp.astimezone().strftime("%b %d, %I:%M %p")


username = st.session_state.get("user_username", "member")
touch_presence(username)
conversations = list_conversations(username)
conversation_by_id = {conversation["id"]: conversation for conversation in conversations}

if "chat_conversation_id" not in st.session_state and conversations:
    st.session_state.chat_conversation_id = conversations[0]["id"]

st.markdown(
    """
    <div class="chat_header">
        <div><span class="eyebrow">STUDY TOGETHER</span><h1>Chat</h1><p>Ask questions, share notes, and keep your learning moving.</p></div>
        <span class="chat_status"><span></span>Refresh-based live chat</span>
    </div>
    """,
    unsafe_allow_html=True,
)

left_column, right_column = st.columns([0.85, 1.8], gap="large")
with left_column:
    st.markdown('<div class="chat_panel_heading"><h2>Conversations</h2></div>', unsafe_allow_html=True)
    with st.expander("Start a conversation", expanded=not conversations):
        chat_users = list_chat_users(username)
        group_options = {f'{user["name"]} (@{user["username"]})': user["username"] for user in chat_users}
        mate_options = {f'{mate["name"]} (@{mate["username"]})': mate["username"] for mate in list_mates(username)}
        if mate_options:
            selected_label = st.selectbox("Message a mate", list(mate_options), key="new_chat_user")
            if st.button("Start direct chat", use_container_width=True, type="primary"):
                conversation_id = create_direct_conversation(username, mate_options[selected_label])
                if conversation_id:
                    st.session_state.chat_conversation_id = conversation_id
                    st.rerun()
        else:
            st.info("Direct chat is available after a mate request is accepted.")

        with st.form("new_group_form"):
            group_title = st.text_input("Study group name", placeholder="e.g. Biology revision")
            group_users = st.multiselect("Invite members", list(group_options), key="new_group_users")
            if st.form_submit_button("Create study group", use_container_width=True):
                members = [group_options[label] for label in group_users]
                conversation_id = create_group_conversation(username, group_title, members)
                if conversation_id:
                    st.session_state.chat_conversation_id = conversation_id
                    st.rerun()
                else:
                    st.error("Choose at least one member and a group name.")

    if conversations:
        for conversation in conversations:
            if conversation["kind"] == "group":
                title = conversation["title"]
            else:
                other = next((person for person in conversation["participants"] if person["username"] != username), None)
                title = (other or {}).get("name") or "Direct message"
            unread = f' · {conversation["unread"]} new' if conversation["unread"] else ""
            last_message = conversation.get("last_message")
            preview = (last_message or {}).get("body") or "Shared a note"
            preview = preview[:42] + ("..." if len(preview) > 42 else "")
            button_label = f"{title}{unread}\n{preview}"
            if st.button(button_label, key=f"conversation_{conversation['id']}", use_container_width=True):
                st.session_state.chat_conversation_id = conversation["id"]
                st.rerun()
    else:
        st.markdown('<div class="chat_empty_small">Your conversations will appear here.</div>', unsafe_allow_html=True)

with right_column:
    selected_id = st.session_state.get("chat_conversation_id")
    selected_conversation = conversation_by_id.get(selected_id)
    if selected_conversation is None:
        st.markdown('<div class="chat_empty_state"><h2>Start a conversation</h2><p>Choose someone from the left to begin a focused study chat.</p></div>', unsafe_allow_html=True)
    else:
        mark_conversation_read(selected_id, username)
        if selected_conversation["kind"] == "group":
            conversation_title = selected_conversation["title"]
            subtitle = f'{len(selected_conversation["participants"])} members'
        else:
            other = next((person for person in selected_conversation["participants"] if person["username"] != username), None)
            conversation_title = (other or {}).get("name") or "Direct message"
            other_username = (other or {}).get("username", "")
            subtitle = f'@{other_username} · {"online" if is_user_online(other_username) else "offline"}'
        st.markdown(f'<div class="conversation_header"><div><h2>{html.escape(conversation_title)}</h2><span>{html.escape(subtitle)}</span></div><span class="conversation_live">Live when active</span></div>', unsafe_allow_html=True)

        messages = get_messages(selected_id, username)
        if not messages:
            st.markdown('<div class="chat_empty_state compact"><h3>No messages yet</h3><p>Share a question or a useful note to get things started.</p></div>', unsafe_allow_html=True)
        for message in messages:
            is_mine = message["sender_username"] == username
            with st.chat_message("user" if is_mine else "assistant"):
                if message["body"]:
                    st.markdown(message["body"])
                if message["shared_note_filename"]:
                    note_path = f'notes/{message["shared_note_owner"]}/{message["shared_note_filename"]}'
                    st.markdown(f'**Shared note:** `{html.escape(message["shared_note_filename"])}`')
                    try:
                        st.image(note_path, use_container_width=True)
                    except Exception:
                        st.caption("This shared note is no longer available.")
                st.caption(f'{"You" if is_mine else "@" + message["sender_username"]} · {format_time(message["created_at"])}')

        shareable_notes = list_shareable_notes(username)
        if shareable_notes:
            note_labels = {path.name: path for path in shareable_notes}
            note_choice = st.selectbox("Share one of your notes", ["Choose a note..."] + list(note_labels), key=f"share_note_{selected_id}")
            if note_choice != "Choose a note..." and st.button("Share selected note", key=f"share_button_{selected_id}", use_container_width=True):
                send_message(selected_id, username, note_owner=username, note_filename=note_labels[note_choice].name)
                st.rerun()

        message_body = st.chat_input("Write a message...", key=f"chat_input_{selected_id}")
        if message_body:
            send_message(selected_id, username, body=message_body)
            st.rerun()

        other_members = [person for person in selected_conversation["participants"] if person["username"] != username]
        with st.expander("Conversation safety"):
            if other_members:
                safety_options = {f'{person["name"]} (@{person["username"]})': person["username"] for person in other_members}
                safety_label = st.selectbox("Member", list(safety_options), key=f"safety_member_{selected_id}")
                safety_username = safety_options[safety_label]
                if st.button("Block member", key=f"block_{selected_id}"):
                    block_user(username, safety_username)
                    st.success("Member blocked. New conversations with them are disabled.")
                    st.rerun()
                report_reason = st.text_input("Report reason", key=f"report_reason_{selected_id}")
                if st.button("Report member", key=f"report_{selected_id}"):
                    if report_user(username, safety_username, selected_id, report_reason):
                        st.success("Report submitted for review.")
                    else:
                        st.warning("Add a short reason before reporting.")

st.markdown('<div class="chat_refresh_hint">Use Refresh in your browser or revisit Chat to check for new messages.</div>', unsafe_allow_html=True)
render_app_footer()