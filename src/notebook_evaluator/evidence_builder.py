from .notebook_parser import compact_notebook


def build_evidence(student: dict, solution: dict, rubric: dict) -> dict:
    return {
        "student_identity": {"id": student.get("id", ""), "name": student.get("name", "")},
        "student_notebook": compact_notebook(student, include_outputs=True),
        "reference_notebook": compact_notebook(solution, include_outputs=True),
        "rubric": rubric,
        "policy": {
            "execute_notebooks": False,
            "missing_saved_output_is_not_a_deduction": True,
            "correct_alternative_implementation_is_acceptable": True,
            "missing_required_task_zero_when_absence_is_clear": True,
            "beginner_friendly_partial_credit": True,
            "manual_review_for_ambiguous_mapping": True,
        },
    }
