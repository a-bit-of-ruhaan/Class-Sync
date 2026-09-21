import base64
import html

import streamlit as st

from backend.ai_api import summarizer_text
from backend.auth import require_auth
from backend.chat import list_mates
from backend.games import create_quiz, get_leaderboard, list_quizzes, parse_quiz_response, record_attempt
from backend.note_summarizer import extract_text_from_docx, extract_text_from_pdf
from backend.ui import render_app_footer, render_sidebar


st.set_page_config(page_title="Study Games", layout="wide", initial_sidebar_state="expanded")
require_auth()
render_sidebar("games")

with open("styles/games.css", encoding="utf-8") as file:
    page_css = file.read()
with open("images/backg.png", "rb") as file:
    background_image = base64.b64encode(file.read()).decode("ascii")
st.markdown(
    f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
    unsafe_allow_html=True,
)


def extract_document(uploaded_file):
    content = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(content)
    if name.endswith(".docx"):
        return extract_text_from_docx(content)
    return content.decode("utf-8", errors="ignore")


username = st.session_state.get("user_username", "member")
st.markdown(
    """
    <section class="games_header">
        <span class="eyebrow">PLAY TO REMEMBER</span>
        <h1>Study Games</h1>
        <p>Turn your notes into friendly competition and make revision a little more memorable.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

create_tab, play_tab, leaderboard_tab = st.tabs(["Create game", "Play", "Leaderboard"])
with create_tab:
    st.markdown('<div class="game_panel"><h2>Generate a quiz from your notes</h2><p>Upload a document and Smart Sum will create a multiple-choice game grounded in its contents.</p></div>', unsafe_allow_html=True)
    source_file = st.file_uploader("Quiz source", type=["pdf", "docx", "txt"], key="game_source")
    game_title = st.text_input("Game title", placeholder="e.g. Biology fundamentals")
    question_count = st.slider("Questions", min_value=3, max_value=10, value=5)
    if st.button("Generate study game", type="primary", use_container_width=True):
        if source_file is None:
            st.warning("Upload a document first.")
        else:
            with st.spinner("Building your study game..."):
                try:
                    document_text = extract_document(source_file)
                    response = summarizer_text(
                        text=f"Create exactly {question_count} multiple-choice quiz questions from the document. Return only valid JSON in this shape: {{\"questions\": [{{\"question\": \"...\", \"options\": [\"...\", \"...\"], \"answer\": 0, \"explanation\": \"...\"}}]}}. The answer must be a zero-based option index. Make questions test understanding, not trivia.",
                        document_text=document_text,
                        feature="quiz",
                    )
                    quiz = parse_quiz_response(response, question_limit=question_count)
                    game_id = create_quiz(game_title or source_file.name, quiz["questions"], username)
                    st.session_state.generated_game_id = game_id
                    st.success("Study game created. Open Play to try it.")
                except Exception as error:
                    st.error(f"The study game could not be created: {error}")
    if st.session_state.get("generated_game_id"):
        st.info("Your latest game is ready in the Play tab.")

quizzes = list_quizzes()
with play_tab:
    if not quizzes:
        st.markdown('<div class="game_empty"><h2>No games yet</h2><p>Create one from a PDF, DOCX, or TXT document to start playing.</p></div>', unsafe_allow_html=True)
    else:
        game_options = {f'{game["title"]} · {len(game["questions"])} questions': game for game in quizzes}
        selected_game_label = st.selectbox("Choose a game", list(game_options), key="selected_game")
        selected_game = game_options[selected_game_label]
        if st.session_state.get("game_result", {}).get("game_id") != selected_game["id"]:
            st.session_state.pop("game_result", None)
        with st.form(f"quiz_form_{selected_game['id']}"):
            answers = []
            for index, question in enumerate(selected_game["questions"]):
                st.markdown(f'**{index + 1}. {html.escape(question["question"])}**')
                answers.append(st.radio("Choose an answer", question["options"], key=f'game_{selected_game["id"]}_q_{index}', label_visibility="collapsed"))
            submitted = st.form_submit_button("Submit answers", type="primary", use_container_width=True)
        if submitted:
            score = sum(answer == question["options"][question["answer"]] for answer, question in zip(answers, selected_game["questions"]))
            record_attempt(selected_game["id"], username, score, len(selected_game["questions"]))
            st.session_state.game_result = {"game_id": selected_game["id"], "score": score, "total": len(selected_game["questions"]), "answers": answers}
            st.rerun()
        result = st.session_state.get("game_result")
        if result and result.get("game_id") == selected_game["id"]:
            st.markdown(f'<div class="game_result"><strong>{result["score"]}/{result["total"]}</strong><span>{round(result["score"] / result["total"] * 100)}% correct</span></div>', unsafe_allow_html=True)
            with st.expander("Review answers", expanded=True):
                for index, question in enumerate(selected_game["questions"]):
                    correct = question["options"][question["answer"]]
                    chosen = result["answers"][index]
                    st.markdown(f'**{index + 1}. {"Correct" if chosen == correct else "Review this"}** - {html.escape(question.get("explanation", ""))}')

with leaderboard_tab:
    if not quizzes:
        st.info("Create and complete a game to start the leaderboard.")
    else:
        leaderboard_game_label = st.selectbox("Leaderboard game", list({f'{game["title"]} · {len(game["questions"])} questions': game for game in quizzes}), key="leaderboard_game")
        leaderboard_game = {f'{game["title"]} · {len(game["questions"])} questions': game for game in quizzes}[leaderboard_game_label]
        scope = st.radio("Show scores", ["Everyone", "Mates only"], horizontal=True)
        allowed_users = None
        if scope == "Mates only":
            allowed_users = [username] + [mate["username"] for mate in list_mates(username)]
        scores = get_leaderboard(leaderboard_game["id"], allowed_users)
        if not scores:
            st.info("No completed attempts in this leaderboard yet.")
        else:
            for index, score in enumerate(scores, start=1):
                percentage = round(score["percentage"] * 100)
                st.markdown(f'<div class="leaderboard_row"><strong>#{index}</strong><span>{html.escape(score.get("name") or score["username"])} <small>@{html.escape(score["username"])}</small></span><b>{score["score"]}/{score["total"]} · {percentage}%</b></div>', unsafe_allow_html=True)

render_app_footer()