from pathlib import Path
from notebook_evaluator.rubric_parser import load_rubric


def test_load_project_rubric():
    project_root = Path(__file__).resolve().parents[1]
    rubric = load_rubric(project_root / "rubric.md")
    assert rubric["total_marks"] == 8
    assert len(rubric["tasks"]) == 7
    assert sum(t["max_marks"] for t in rubric["tasks"]) == 8
