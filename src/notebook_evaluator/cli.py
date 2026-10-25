from __future__ import annotations
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from .config import load_config
from .notebook_parser import parse_notebook
from .rubric_parser import load_rubric
from .state_store import StateStore
from .batch_runner import grade_one
from .exporter import export_csv, export_xlsx

LOG = logging.getLogger("notebook_evaluator")


def _load_dotenv(project_root: Path):
    env_path = project_root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _resolve(root: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else root / p


def _inputs(config, args):
    root = config["_project_root"]
    notebooks_dir = _resolve(root, args.notebooks or config["inputs"]["notebooks_dir"])
    rubric_path = _resolve(root, args.rubric or config["inputs"]["rubric_file"])
    solution_path = _resolve(root, args.solution or config["inputs"]["solution_file"])
    return root, notebooks_dir, rubric_path, solution_path


def run_inspect(config, args):
    root, notebooks_dir, rubric_path, solution_path = _inputs(config, args)
    rubric = load_rubric(rubric_path)
    solution = parse_notebook(solution_path)
    print(f"Root: {root}")
    print(f"Rubric: {rubric_path} ({len(rubric['tasks'])} tasks, {rubric['total_marks']} marks)")
    print(f"Solution: {solution_path} ({len(solution['cells'])} cells)")
    print(f"Student notebook directory: {notebooks_dir}")
    paths = sorted(notebooks_dir.glob("*.ipynb")) if notebooks_dir.exists() else []
    print(f"Found {len(paths)} student notebook(s)")
    for path in paths:
        try:
            nb = parse_notebook(path)
            print(f"- {path.name}: ID={nb['id'] or '[MISSING]'}; Name={nb['name'] or '[MISSING]'}; cells={len(nb['cells'])}")
        except Exception as exc:
            print(f"- {path.name}: PARSE ERROR: {exc}")


def run_evaluate(config, args):
    root, notebooks_dir, rubric_path, solution_path = _inputs(config, args)
    rubric = load_rubric(rubric_path)
    solution = parse_notebook(solution_path)
    if not notebooks_dir.exists():
        raise SystemExit(f"Notebook directory does not exist: {notebooks_dir}")
    paths = sorted(notebooks_dir.glob("*.ipynb"))
    if not paths:
        raise SystemExit(f"No .ipynb files found in {notebooks_dir}")

    students = []
    for path in paths:
        try:
            student = parse_notebook(path)
            if not student.get("id") or not student.get("name"):
                LOG.warning("Identity incomplete in %s; will require review", path.name)
            students.append(student)
        except Exception as exc:
            LOG.error("Skipping unreadable notebook %s: %s", path.name, exc)

    records_dir = _resolve(root, config.get("artifacts", {}).get("records_dir", "artifacts/grading_records"))
    state_store = StateStore(records_dir)

    if args.dry_run:
        out_dir = _resolve(root, config.get("artifacts", {}).get("normalized_dir", "artifacts/normalized"))
        out_dir.mkdir(parents=True, exist_ok=True)
        for student in students:
            output = {
                "file_name": student["file_name"],
                "student_id": student["id"],
                "student_name": student["name"],
                "cell_count": len(student["cells"]),
                "rubric_task_ids": [t["id"] for t in rubric["tasks"]],
                "execute_notebooks": False,
            }
            (out_dir / (Path(student["file_name"]).stem + ".dryrun.json")).write_text(
                json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        print(f"Dry run complete: parsed {len(students)} notebooks; no LLM calls made.")
        return

    batch_size = max(1, int(config.get("grading", {}).get("batch_size", 2)))
    records = []
    total_students = len(students)
    run_started = time.monotonic()
    failed_count = 0
    for batch_start in range(0, total_students, batch_size):
        batch = students[batch_start:batch_start + batch_size]
        batch_number = batch_start // batch_size + 1
        total_batches = (total_students + batch_size - 1) // batch_size
        print(f"\n{'=' * 78}\nBATCH {batch_number}/{total_batches} | notebooks {batch_start + 1}-{batch_start + len(batch)} of {total_students}\n{'=' * 78}", flush=True)
        for offset, student in enumerate(batch):
            notebook_number = batch_start + offset + 1
            notebook_started = time.monotonic()
            identity = f"ID={student.get('id') or '[missing]'} | Name={student.get('name') or '[missing]'}"
            print(f"\n[{notebook_number}/{total_students}] START: {student['file_name']}\n    {identity}", flush=True)

            def progress(message):
                elapsed = time.monotonic() - notebook_started
                print(f"    [{elapsed:6.1f}s] {message}", flush=True)

            try:
                record = grade_one(student, solution, rubric, config, state_store, force=args.force, progress=progress)
                if not record.get("grade", {}).get("student_id"):
                    record["grade"]["student_id"] = student.get("id", "")
                if not record.get("grade", {}).get("student_name"):
                    record["grade"]["student_name"] = student.get("name", "")
                if not student.get("id") or not student.get("name"):
                    record["grade"]["manual_review"] = True
                    record["grade"].setdefault("review_reasons", []).append("Could not reliably extract ID/Name from notebook.")
                state_store.save(student.get("id", ""), student["file_name"], record)
                records.append(record)
                elapsed = time.monotonic() - notebook_started
                completed = notebook_number
                remaining = total_students - completed
                print(f"[{notebook_number}/{total_students}] COMPLETE in {elapsed:.1f}s | total={record.get('grade', {}).get('total_marks', '?')}/{rubric['total_marks']} | manual_review={record.get('grade', {}).get('manual_review', False)} | remaining={remaining}", flush=True)
            except Exception as exc:
                LOG.exception("Failed to grade %s", student["file_name"])
                failure = {
                    "status": "failed",
                    "student_file": student["file_name"],
                    "grade": {
                        "student_id": student.get("id", ""),
                        "student_name": student.get("name", ""),
                        "tasks": [],
                        "total_marks": "",
                        "manual_review": True,
                        "review_reasons": [f"Evaluation failed: {exc}"],
                    },
                    "verifier": {},
                }
                state_store.save(student.get("id", ""), student["file_name"], failure)
                records.append(failure)
                failed_count += 1
                print(f"[{notebook_number}/{total_students}] FAILED after {time.monotonic() - notebook_started:.1f}s: {exc}", flush=True)
                print("    Result checkpointed; proceeding to the next notebook.", flush=True)

    out_dir = _resolve(root, config.get("output", {}).get("directory", "results"))
    csv_path = out_dir / config.get("output", {}).get("csv_file", "grades.csv")
    xlsx_path = out_dir / config.get("output", {}).get("xlsx_file", "grades.xlsx")
    # Include failed records in the export so no student silently disappears.
    export_csv(records, rubric, csv_path)
    export_xlsx(records, rubric, xlsx_path)
    failed_count = sum(1 for r in records if not r.get("grade", {}).get("tasks"))
    print(f"Finished. CSV: {csv_path}")
    print(f"Finished. XLSX: {xlsx_path}")
    total_elapsed = time.monotonic() - run_started
    print(f"Records exported: {len(records)}; failed records flagged for review: {failed_count}")
    print(f"Total runtime: {total_elapsed / 60:.1f} minutes")


def main():
    parser = argparse.ArgumentParser(prog="notebook-evaluator")
    parser.add_argument("--config", default="config/evaluator.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "evaluate", "export"):
        p = sub.add_parser(command)
        p.add_argument("--notebooks")
        p.add_argument("--rubric")
        p.add_argument("--solution")
        if command == "evaluate":
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--force", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    root = config["_project_root"]
    _load_dotenv(root)

    if args.command == "inspect":
        run_inspect(config, args)
    elif args.command == "evaluate":
        run_evaluate(config, args)
    elif args.command == "export":
        # Export all saved records. Failed records without task grades are excluded.
        rubric_path = _resolve(root, args.rubric or config["inputs"]["rubric_file"])
        rubric = load_rubric(rubric_path)
        records_dir = _resolve(root, config.get("artifacts", {}).get("records_dir", "artifacts/grading_records"))
        records = []
        for p in sorted(records_dir.glob("*.json")):
            try:
                r = json.loads(p.read_text(encoding="utf-8"))
                records.append(r)
            except Exception:
                continue
        out_dir = _resolve(root, config.get("output", {}).get("directory", "results"))
        export_csv(records, rubric, out_dir / config.get("output", {}).get("csv_file", "grades.csv"))
        export_xlsx(records, rubric, out_dir / config.get("output", {}).get("xlsx_file", "grades.xlsx"))
        print(f"Exported {len(records)} records to {out_dir}")


if __name__ == "__main__":
    main()
