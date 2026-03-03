import os
import re
from pathlib import Path
from typing import Any

import yaml


def _substitute_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(item) for item in value]
    if isinstance(value, str):
        pattern = re.compile(r"\$\{([^}]+)\}")

        def _replace(match: re.Match) -> str:
            s = match.group(1)
            if ":-" in s:
                key, default = s.split(":-", 1)
                return os.environ.get(key.strip(), default.strip())
            return os.environ.get(s, "")

        return pattern.sub(_replace, value)
    return value


def load_settings(settings_dir: Path | None = None) -> dict:
    if settings_dir is None:
        settings_dir = Path.cwd() / "settings"
        if not settings_dir.exists():
            settings_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "settings"
    base_path = settings_dir / "base.yaml"
    with open(base_path, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return _substitute_env(config)
