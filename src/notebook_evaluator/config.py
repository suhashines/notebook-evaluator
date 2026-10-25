from pathlib import Path
import os
import yaml


def load_config(path: str | Path) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    root = Path(config.get("project_root", "."))
    if not root.is_absolute():
        root = (path.parent.parent / root).resolve()
    config["_project_root"] = root
    return config


def env_value(name: str, default=None):
    value = os.getenv(name)
    return value if value not in (None, "") else default
