from notebook_evaluator.exporter import flatten_record


def test_flatten_record():
    rubric = {"tasks": [{"id": "CW1", "max_marks": 1.0}]}
    record = {"grade": {
        "student_id": "123", "student_name": "A",
        "tasks": [{"task_id": "CW1", "marks_awarded": 1.0, "reasoning": "Correct"}],
        "total_marks": 1.0, "manual_review": False, "review_reasons": []
    }}
    row = flatten_record(record, rubric)
    assert row["ID"] == "123"
    assert row["CW1 Marks"] == 1.0
