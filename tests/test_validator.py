import pytest
from notebook_evaluator.validator import validate_judge_result


@pytest.fixture
def rubric():
    return {
        "total_marks": 2,
        "tasks": [
            {"id": "A", "max_marks": 1.0},
            {"id": "B", "max_marks": 1.0},
        ],
    }


def result(a=1.0, b=0.5):
    return {
        "student_id": "12345678",
        "student_name": "Student",
        "tasks": [
            {"task_id": "A", "marks_awarded": a, "maximum_marks": 1.0, "reasoning": "Evidence A"},
            {"task_id": "B", "marks_awarded": b, "maximum_marks": 1.0, "reasoning": "Evidence B"},
        ],
    }


def test_valid_scores(rubric):
    out = validate_judge_result(result(), rubric)
    assert out["total_marks"] == 1.5


def test_rejects_score_above_maximum(rubric):
    with pytest.raises(ValueError):
        validate_judge_result(result(a=1.5), rubric)


def test_rejects_non_half_increment(rubric):
    with pytest.raises(ValueError):
        validate_judge_result(result(a=0.75), rubric)


def test_rejects_missing_task(rubric):
    r = result()
    r["tasks"] = r["tasks"][:1]
    with pytest.raises(ValueError):
        validate_judge_result(r, rubric)
