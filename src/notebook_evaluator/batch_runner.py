from __future__ import annotations
import json
import logging
import re
import time
from pathlib import Path

from .evidence_builder import build_evidence
from .llm_client import chat_completion
from .prompts import judge_messages, verifier_messages
from .state_store import StateStore
from .validator import validate_judge_result, apply_verifier

logger = logging.getLogger(__name__)


def _json_from_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise ValueError("LLM response did not contain valid JSON")


def _call_with_retries(messages, config, temperature, max_retries, stage_callback=None, stage_name="LLM request"):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            if stage_callback:
                stage_callback(f"{stage_name}: sending request (attempt {attempt + 1}/{max_retries + 1})")
            started = time.monotonic()
            response = chat_completion(messages, config, temperature=temperature)
            elapsed = time.monotonic() - started
            if stage_callback:
                stage_callback(f"{stage_name}: response received after {elapsed:.1f}s; parsing JSON")
            return _json_from_response(response)
        except Exception as exc:
            last_error = exc
            logger.warning("LLM call failed (attempt %s/%s): %s", attempt + 1, max_retries + 1, exc)
            if stage_callback:
                stage_callback(f"{stage_name}: failed on attempt {attempt + 1}: {exc}")
            if attempt < max_retries:
                delay = min(2 ** attempt, 8)
                if stage_callback:
                    stage_callback(f"{stage_name}: retrying in {delay}s")
                time.sleep(delay)
    raise RuntimeError(f"LLM call failed after retries: {last_error}")


def grade_one(student, solution, rubric, config, state_store: StateStore, force=False, progress=None):
    def report(message):
        if progress:
            progress(message)
    cached = state_store.load(student.get("id", ""), student["file_name"])
    if cached and not force and cached.get("status") == "complete":
        logger.info("Skipping completed notebook %s", student["file_name"])
        report("Previously completed result found; skipping LLM calls")
        return cached

    report("Preparing evidence from notebook, saved outputs, and reference solution")
    evidence = build_evidence(student, solution, rubric)
    normalized_dir = config.get("artifacts", {}).get("normalized_dir", "artifacts/normalized")
    normalized_path = Path(normalized_dir) / (Path(student["file_name"]).stem + ".json")
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    report(f"Evidence prepared and saved to {normalized_path}")

    grading = config.get("grading", {})
    report("Judge stage started; waiting for model assessment")
    judge = _call_with_retries(
        judge_messages(evidence), config,
        float(grading.get("judge_temperature", 0)),
        int(grading.get("max_retries", 2)),
        stage_callback=report,
        stage_name="Judge",
    )
    increment = float(grading.get("minimum_mark_increment", 0.5))
    report("Judge response received; validating task marks and required task IDs")
    judge = validate_judge_result(judge, rubric, increment)
    report(f"Judge assessment validated: {len(judge['tasks'])}/{len(rubric['tasks'])} tasks returned")
    for task in judge["tasks"]:
        report(f"  {task['task_id']}: {task['marks_awarded']}/{task['maximum_marks']} — {task['reasoning']}")

    verifier = {}
    if grading.get("verify_each_submission", True):
        report("Verifier stage started; independently checking the assessment")
        verifier = _call_with_retries(
            verifier_messages(evidence, judge), config,
            float(grading.get("verifier_temperature", 0)),
            int(grading.get("max_retries", 2)),
            stage_callback=report,
            stage_name="Verifier",
        )
        report("Verifier response received; reconciling disagreements")
        judge = apply_verifier(judge, verifier, rubric, increment)
        # Re-validate final marks after verifier recommendations.
        judge = validate_judge_result(judge, rubric, increment)
        report(f"Verification complete; total={judge['total_marks']}/{rubric['total_marks']}; manual_review={judge.get('manual_review', False)}")

    record = {
        "status": "complete",
        "student_file": student["file_name"],
        "grade": judge,
        "verifier": verifier,
        "model": __import__("os").getenv("LLM_MODEL", ""),
    }
    state_store.save(student.get("id", ""), student["file_name"], record)
    report("Grading record checkpointed to disk")
    return record
