"""
tests/test_exam_history.py — Test services/exam_history.py.

Dùng monkeypatch để redirect history root vào tmp_path.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def tmp_history(monkeypatch, tmp_path):
    from services import exam_history
    fake_root = tmp_path / "exam_history"
    fake_root.mkdir()
    monkeypatch.setattr(exam_history, "_history_root", lambda: fake_root)
    return fake_root


# ── Mock ExamData (để khỏi import core.models) ────────────────────────────

class _FakeExam:
    def __init__(self, title="Test Exam", subject="Toán", grade="12",
                 year="2026", n=3, qtype="TN", points=0.25):
        self.exam_title = title
        self.subject = subject
        self.grade = grade
        self.semester = "II"
        self.year = year
        self.time = "90 phút"
        self.school = "THPT V5"
        self.teacher = "Tổ Toán"
        self.questions = [
            _FakeQ(qtype=qtype, topic=f"Topic {i}", question=f"Câu {i}?",
                   points=points)
            for i in range(n)
        ]


class _FakeQ:
    def __init__(self, qtype="TN", topic="", question="", points=0.25):
        self.qtype = qtype
        self.topic = topic
        self.question = question
        self.points = points

    def to_dict(self):
        return {
            "qtype": self.qtype, "topic": self.topic,
            "question": self.question, "points": self.points,
        }


# ══════════════════════════════════════════════════════════════════════════
# SNAPSHOT
# ══════════════════════════════════════════════════════════════════════════

def test_snapshot_creates_v1(tmp_history):
    from services import exam_history
    exam = _FakeExam(n=3)
    info = exam_history.snapshot(exam, source="ai", note="initial")
    assert info is not None
    assert info.version == 1
    assert info.source == "ai"
    assert info.n_questions == 3
    assert info.n_tn == 3


def test_snapshot_increments_version(tmp_history):
    from services import exam_history
    exam = _FakeExam(n=2)
    v1 = exam_history.snapshot(exam, source="ai", note="v1")
    # Tạo exam khác (content khác → mới)
    exam2 = _FakeExam(n=5)
    v2 = exam_history.snapshot(exam2, source="manual", note="v2")
    assert v1.version == 1
    assert v2.version == 2


def test_snapshot_dedupes_identical(tmp_history):
    """Snapshot 2 lần liên tiếp với content giống nhau → KHÔNG tạo v2."""
    from services import exam_history
    exam = _FakeExam(n=3)
    v1 = exam_history.snapshot(exam, source="ai")
    v_dup = exam_history.snapshot(exam, source="ai")  # giống
    assert v_dup.version == v1.version  # dedupe → return v1


def test_snapshot_total_points(tmp_history):
    from services import exam_history
    exam = _FakeExam(n=4, points=0.5)   # 4 câu × 0.5 = 2.0
    info = exam_history.snapshot(exam)
    assert abs(info.total_points - 2.0) < 0.01


# ══════════════════════════════════════════════════════════════════════════
# LIST + RESTORE
# ══════════════════════════════════════════════════════════════════════════

def test_list_versions_sorted_desc(tmp_history):
    from services import exam_history
    e1 = _FakeExam(n=1)
    e2 = _FakeExam(n=2)
    e3 = _FakeExam(n=3)
    exam_history.snapshot(e1, source="ai")
    exam_history.snapshot(e2, source="ai")
    exam_history.snapshot(e3, source="manual")

    exam_id = exam_history._exam_id_from_data(e1)
    versions = exam_history.list_versions(exam_id)
    assert len(versions) == 3
    # Mới nhất → cũ
    assert versions[0].version == 3
    assert versions[1].version == 2
    assert versions[2].version == 1
    # Source đúng
    assert versions[0].source == "manual"


def test_restore_returns_data(tmp_history):
    from services import exam_history
    exam = _FakeExam(n=5, points=1.0)
    info = exam_history.snapshot(exam, source="ai")
    exam_id = exam_history._exam_id_from_data(exam)
    data = exam_history.restore(exam_id, info.version)
    assert data is not None
    assert data["exam_title"] == exam.exam_title
    assert data["school"] == "THPT V5"
    assert data["teacher"] == "Tổ Toán"
    assert len(data["questions"]) == 5


def test_restore_nonexistent_returns_none(tmp_history):
    from services import exam_history
    assert exam_history.restore("doesnt_exist", 1) is None


def test_restore_latest(tmp_history):
    from services import exam_history
    e1 = _FakeExam(n=1)
    e2 = _FakeExam(n=2)
    exam_history.snapshot(e1)
    exam_history.snapshot(e2)
    eid = exam_history._exam_id_from_data(e1)
    latest = exam_history.restore_latest(eid)
    assert latest is not None
    # latest = e2 (n=2 questions)
    assert len(latest["questions"]) == 2


# ══════════════════════════════════════════════════════════════════════════
# COMPARE
# ══════════════════════════════════════════════════════════════════════════

def test_compare_different_versions(tmp_history):
    from services import exam_history
    e1 = _FakeExam(n=3, points=0.25)   # 0.75đ
    e2 = _FakeExam(n=4, points=0.25)   # 1.0đ
    v1 = exam_history.snapshot(e1, source="ai")
    v2 = exam_history.snapshot(e2, source="ai")
    eid = exam_history._exam_id_from_data(e1)
    diff = exam_history.compare(eid, v1.version, v2.version)
    assert "error" not in diff
    # Points tăng 0.25
    assert abs(diff["pts_diff"] - 0.25) < 0.01
    # Q added: e2 có thêm Topic 3 (e1 chỉ có Topic 0,1,2)
    assert diff["q_added"] >= 1


def test_compare_invalid_version(tmp_history):
    from services import exam_history
    exam_history.snapshot(_FakeExam())
    eid = exam_history._exam_id_from_data(_FakeExam())
    diff = exam_history.compare(eid, 999, 1)
    assert "error" in diff


# ══════════════════════════════════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════════════════════════════════

def test_delete_version(tmp_history):
    from services import exam_history
    e1 = _FakeExam(n=1)
    e2 = _FakeExam(n=2)
    v1 = exam_history.snapshot(e1)
    v2 = exam_history.snapshot(e2)
    eid = exam_history._exam_id_from_data(e1)
    assert exam_history.delete_version(eid, v1.version) is True
    remaining = exam_history.list_versions(eid)
    assert len(remaining) == 1
    assert remaining[0].version == v2.version


def test_delete_exam_history(tmp_history):
    from services import exam_history
    e = _FakeExam()
    exam_history.snapshot(e)
    e2 = _FakeExam(n=4)
    exam_history.snapshot(e2)
    eid = exam_history._exam_id_from_data(e)
    n = exam_history.delete_exam_history(eid)
    assert n == 2
    assert exam_history.list_versions(eid) == []


# ══════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════

def test_stats_empty(tmp_history):
    from services import exam_history
    s = exam_history.stats()
    assert s["n_exams"] == 0
    assert s["total_versions"] == 0


def test_stats_with_data(tmp_history):
    from services import exam_history
    e1 = _FakeExam(title="Exam A")
    e2 = _FakeExam(title="Exam B")
    exam_history.snapshot(e1)
    exam_history.snapshot(_FakeExam(title="Exam A", n=4))
    exam_history.snapshot(e2)
    s = exam_history.stats()
    assert s["n_exams"] == 2
    assert s["total_versions"] == 3


def test_list_all_exams(tmp_history):
    from services import exam_history
    exam_history.snapshot(_FakeExam(title="Exam X"))
    exam_history.snapshot(_FakeExam(title="Exam Y"))
    items = exam_history.list_all_exams()
    assert len(items) == 2
    # Mỗi item: (exam_id, n_versions, latest_ts)
    titles = [i[0] for i in items]
    assert any("Exam_X" in t for t in titles)
    assert any("Exam_Y" in t for t in titles)
