from pathlib import Path
import re
import yaml


def load_rubric(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not match:
        raise ValueError("rubric.md must begin with YAML front matter delimited by ---")
    data = yaml.safe_load(match.group(1)) or {}
    tasks = data.get("tasks", [])
    if not tasks:
        raise ValueError("No tasks found in rubric.md front matter")
    ids = [t.get("id") for t in tasks]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        raise ValueError("Task IDs must be present and unique")
    total = round(sum(float(t["max_marks"]) for t in tasks), 2)
    if abs(total - float(data.get("total_marks", total))) > 1e-8:
        raise ValueError(f"Rubric task maxima sum to {total}, not total_marks={data.get('total_marks')}")
    return data
