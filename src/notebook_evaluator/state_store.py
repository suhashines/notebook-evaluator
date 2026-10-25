from pathlib import Path
import json
import re


def safe_stem(text: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", text or "unknown").strip("._")
    return stem[:100] or "unknown"


class StateStore:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, student_id: str, file_name: str) -> Path:
        return self.directory / f"{safe_stem(student_id)}__{safe_stem(file_name)}.json"

    def load(self, student_id: str, file_name: str):
        path = self.path_for(student_id, file_name)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def save(self, student_id: str, file_name: str, record: dict):
        path = self.path_for(student_id, file_name)
        temp = path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
        return path
