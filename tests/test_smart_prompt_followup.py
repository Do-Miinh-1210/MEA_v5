from __future__ import annotations

from core.models import MatrixData, MatrixRow
from core.smart_prompt import (
    clone_matrix,
    diff_matrices,
    followup_modify_matrix,
    format_matrix_diff,
)


def _matrix() -> MatrixData:
    return MatrixData(
        title="De kiem tra",
        time_str="45 phut",
        rows=[
            MatrixRow("1", "Ham so", "NB", "TN", ["TN1"], "Nhan biet ham so", 0.25),
            MatrixRow("2", "Ham so", "TH", "TN", ["TN2"], "Thong hieu ham so", 0.25),
        ],
    )


def test_followup_modify_matrix_does_not_mutate_original_rows():
    matrix = _matrix()

    new_matrix, message = followup_modify_matrix(
        matrix,
        "Tang do kho cau 1",
        ai_call=lambda _prompt: '{"action":"modify","modify":[{"stt":1,"field":"level","new_value":"VD"}]}',
    )

    assert matrix.rows[0].level == "NB"
    assert new_matrix.rows[0].level == "VD"
    assert "Chỉnh" in message


def test_matrix_diff_reports_modified_and_added_rows():
    before = _matrix()
    after = clone_matrix(before)
    after.rows[0].level = "VD"
    after.rows.append(MatrixRow("3", "Tich phan", "TH", "TLN", ["TLN3"], "Tinh tich phan", 0.5))

    diff = diff_matrices(before, after)
    text = format_matrix_diff(diff)

    assert diff["before_count"] == 2
    assert diff["after_count"] == 3
    assert diff["modified"][0]["changes"]["level"]["new"] == "VD"
    assert diff["added"][0]["qtype"] == "TLN"
    assert "~ Câu 1" in text
    assert "+ Câu 3" in text
