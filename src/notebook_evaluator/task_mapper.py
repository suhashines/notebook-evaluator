import re


def detect_task_markers(notebook: dict) -> dict:
    """Heuristic mapping for review/audit; LLM may resolve flexible self-task mapping."""
    markers = {}
    for cell in notebook.get("cells", []):
        src = cell.get("source", "")
        text = src.strip()
        patterns = [
            (r"(?i)#\s*task[_\s-]*([1-4])", "ST"),
            (r"(?i)^#+\s*task\s*([1-4])\b", "ST"),
            (r"(?i)^#+\s*method\s*([1-3])\b", "CW"),
            (r"(?i)method\s*1.*using\s+list", "CW1"),
            (r"(?i)method\s*2.*class", "CW2"),
            (r"(?i)method\s*3.*vandermonde", "CW3"),
        ]
        for pat, prefix in patterns:
            m = re.search(pat, text)
            if m:
                if prefix == "ST":
                    key = f"ST{m.group(1)}"
                elif prefix == "CW":
                    key = f"CW{m.group(1)}"
                else:
                    key = prefix
                markers.setdefault(key, []).append(cell["index"])
    return markers
