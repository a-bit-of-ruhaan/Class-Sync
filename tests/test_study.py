import datetime

from backend import auth
from backend.study import load_study_plan, save_study_plan


def test_study_plan_persists_across_loads(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DATABASE_PATH", tmp_path / "classync.db")
    save_study_plan("alex", "Physics revision", ["Read chapter", "Make flashcards"], datetime.date(2026, 10, 1))

    plan = load_study_plan("alex")

    assert plan["focus"] == "Physics revision"
    assert plan["tasks"][:2] == ["Read chapter", "Make flashcards"]
    assert plan["date"] == datetime.date(2026, 10, 1)