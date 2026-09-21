import pytest

from backend import auth
from backend.games import create_quiz, get_leaderboard, parse_quiz_response, record_attempt


def test_parse_quiz_response_accepts_json_fences_and_normalizes_questions():
    payload = """```json
    {"questions": [{"question": "2 + 2?", "options": ["3", "4"], "answer": 1, "explanation": "Addition."}, {"question": "Sky?", "options": ["Blue", "Green"], "answer": 0}]}
    ```"""

    quiz = parse_quiz_response(payload)

    assert len(quiz["questions"]) == 2
    assert quiz["questions"][0]["answer"] == 1


def test_quiz_attempts_rank_best_scores_and_filter_leaderboard(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    for name, username in (("Alex Morgan", "alex"), ("Sam Lee", "sam"), ("Joe Kim", "joe")):
        assert auth.register_user(name, username, f"{username}@example.com", "password123")[0]
    game_id = create_quiz("Biology basics", [{"question": "Q", "options": ["A", "B"], "answer": 0, "explanation": ""}], "alex")

    assert record_attempt(game_id, "alex", 1, 1)
    assert record_attempt(game_id, "sam", 0, 1)
    assert record_attempt(game_id, "alex", 0, 1)
    assert not record_attempt(game_id, "joe", 2, 1)
    assert [row["username"] for row in get_leaderboard(game_id)] == ["alex", "sam"]
    assert [row["username"] for row in get_leaderboard(game_id, ["sam"])] == ["sam"]


def test_leaderboard_uses_one_consistent_best_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    assert auth.register_user("Alex Morgan", "alex", "alex@example.com", "password123")[0]
    game_id = create_quiz("Mixed totals", [{"question": "Q", "options": ["A", "B"], "answer": 0, "explanation": ""}], "alex")

    assert record_attempt(game_id, "alex", 1, 1)
    assert record_attempt(game_id, "alex", 8, 10)

    score = get_leaderboard(game_id)[0]
    assert score["score"] == 1
    assert score["total"] == 1
    assert score["percentage"] == 1


def test_parse_quiz_response_rejects_invalid_answers():
    with pytest.raises(ValueError):
        parse_quiz_response('{"questions": [{"question": "Q", "options": ["A"], "answer": 0}]}')