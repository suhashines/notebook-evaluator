from __future__ import annotations
import ast
import json
import re
from pathlib import Path


def _source(cell: dict) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else str(src)


def _extract_assignment(code: str, names: list[str]):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                value = node.value
                for target in targets:
                    if isinstance(target, ast.Name) and target.id.upper() in names:
                        try:
                            return ast.literal_eval(value)
                        except Exception:
                            pass
    for name in names:
        pattern = rf"(?im)^\s*{re.escape(name)}\s*=\s*['\"]([^'\"]*)['\"]"
        m = re.search(pattern, code)
        if m:
            return m.group(1)
    return None


def _output_text(output: dict) -> str:
    kind = output.get("output_type", "")
    if kind == "stream":
        return "".join(output.get("text", [])) if isinstance(output.get("text"), list) else str(output.get("text", ""))
    if kind == "error":
        tb = output.get("traceback", [])
        return "ERROR: " + "\n".join(str(x) for x in tb)
    data = output.get("data", {})
    pieces = []
    for mime in ("text/plain", "text/html", "application/json"):
        if mime in data:
            val = data[mime]
            if isinstance(val, list):
                val = "".join(val)
            if isinstance(val, (dict, list)):
                val = json.dumps(val, ensure_ascii=False)
            pieces.append(f"[{mime}] {str(val)}")
    if not pieces and "image/png" in data:
        pieces.append("[image/png output present; image content omitted]")
    if not pieces and "image/jpeg" in data:
        pieces.append("[image/jpeg output present; image content omitted]")
    return "\n".join(pieces)


def parse_notebook(path: str | Path) -> dict:
    path = Path(path)
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Could not parse notebook {path}: {exc}") from exc

    cells = []
    identity_code = []
    for idx, cell in enumerate(notebook.get("cells", [])):
        cell_type = cell.get("cell_type", "unknown")
        source = _source(cell)
        if idx <= 5 and cell_type == "code":
            identity_code.append(source)
        outputs = [_output_text(o) for o in cell.get("outputs", [])] if cell_type == "code" else []
        outputs = [o[:5000] for o in outputs if o.strip()]
        cells.append({
            "index": idx,
            "type": cell_type,
            "source": source,
            "outputs": outputs,
            "execution_count": cell.get("execution_count"),
        })

    id_value = name_value = section_value = None
    for code in identity_code:
        if id_value is None:
            id_value = _extract_assignment(code, ["ID", "STUDENT_ID"])
        if name_value is None:
            name_value = _extract_assignment(code, ["NAME", "STUDENT_NAME"])
        if section_value is None:
            section_value = _extract_assignment(code, ["SECTION", "LAB_SECTION"])
    if id_value is None:
        m = re.search(r"(?<!\d)(\d{7,12})(?!\d)", path.stem)
        id_value = m.group(1) if m else ""
    if name_value is None:
        name_value = ""

    return {
        "file_name": path.name,
        "file_path": str(path),
        "id": str(id_value or "").strip(),
        "name": str(name_value or "").strip(),
        "section": str(section_value or "").strip() if section_value is not None else "",
        "nbformat": notebook.get("nbformat"),
        "cells": cells,
    }


def compact_notebook(notebook: dict, include_outputs: bool = True) -> str:
    parts = [
        f"FILE: {notebook.get('file_name')}",
        f"STUDENT_ID: {notebook.get('id') or '[MISSING]'}",
        f"STUDENT_NAME: {notebook.get('name') or '[MISSING]'}",
    ]
    for cell in notebook.get("cells", []):
        source = cell.get("source", "").strip()
        if not source:
            continue
        # Keep text and code; avoid metadata and bulky embedded binary outputs.
        parts.append(f"\n--- CELL {cell['index']} [{cell['type']}] ---\n{source}")
        if include_outputs and cell.get("outputs"):
            parts.append("SAVED OUTPUTS:\n" + "\n".join(cell["outputs"]))
    return "\n".join(parts)
