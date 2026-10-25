from __future__ import annotations
import math


def _valid_increment(value: float, increment: float) -> bool:
    return abs(value / increment - round(value / increment)) < 1e-7


def validate_judge_result(result: dict, rubric: dict, increment: float = 0.5) -> dict:
    expected = {t["id"]: t for t in rubric["tasks"]}
    received = result.get("tasks")
    if not isinstance(received, list):
        raise ValueError("Judge result tasks must be a list")
    by_id = {}
    for item in received:
        task_id = item.get("task_id")
        if task_id not in expected:
            raise ValueError(f"Unknown task_id in judge result: {task_id}")
        if task_id in by_id:
            raise ValueError(f"Duplicate task_id in judge result: {task_id}")
        by_id[task_id] = item
    missing = set(expected) - set(by_id)
    if missing:
        raise ValueError(f"Judge omitted required tasks: {sorted(missing)}")
    total = 0.0
    for task_id, spec in expected.items():
        item = by_id[task_id]
        maximum = float(spec["max_marks"])
        marks = item.get("marks_awarded")
        if isinstance(marks, bool) or not isinstance(marks, (int, float)) or not math.isfinite(float(marks)):
            raise ValueError(f"Invalid marks for {task_id}")
        marks = float(marks)
        if marks < 0 or marks > maximum:
            raise ValueError(f"Marks for {task_id} outside [0, {maximum}]: {marks}")
        if not _valid_increment(marks, increment):
            raise ValueError(f"Marks for {task_id} must use increments of {increment}: {marks}")
        item["marks_awarded"] = marks
        item["maximum_marks"] = maximum
        if not isinstance(item.get("reasoning"), str) or not item["reasoning"].strip():
            raise ValueError(f"Missing concise reasoning for {task_id}")
        confidence = item.get("confidence", 0.5)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.0
        item["confidence"] = min(1.0, max(0.0, confidence))
        total += marks
    result["tasks"] = [by_id[t["id"]] for t in rubric["tasks"]]
    result["total_marks"] = round(total, 2)
    result.setdefault("manual_review", False)
    result.setdefault("review_reasons", [])
    if any(t.get("manual_review") for t in result["tasks"]):
        result["manual_review"] = True
    return result


def apply_verifier(judge_result: dict, verifier_result: dict, rubric: dict, increment: float = 0.5) -> dict:
    verdicts = {t.get("task_id"): t for t in verifier_result.get("tasks", [])}
    manual = bool(judge_result.get("manual_review")) or bool(verifier_result.get("manual_review"))
    reasons = list(judge_result.get("review_reasons", [])) + list(verifier_result.get("review_reasons", []))
    for task in judge_result["tasks"]:
        verdict = verdicts.get(task["task_id"])
        if not verdict:
            task["manual_review"] = True
            manual = True
            reasons.append(f"Verifier omitted {task['task_id']}")
            continue
        if not verdict.get("approved", False):
            rec = verdict.get("recommended_marks")
            if isinstance(rec, (int, float)) and 0 <= float(rec) <= float(task["maximum_marks"]) and _valid_increment(float(rec), increment):
                task["marks_awarded"] = float(rec)
                task["reasoning"] = str(verdict.get("reasoning") or task["reasoning"])
            task["manual_review"] = True
            manual = True
            reasons.append(f"{task['task_id']}: judge/verifier disagreement")
        if verdict.get("manual_review"):
            task["manual_review"] = True
            manual = True
            if verdict.get("review_reason"):
                reasons.append(f"{task['task_id']}: {verdict['review_reason']}")
    judge_result["total_marks"] = round(sum(t["marks_awarded"] for t in judge_result["tasks"]), 2)
    judge_result["manual_review"] = manual
    judge_result["review_reasons"] = sorted(set(str(x) for x in reasons if x))
    return judge_result
