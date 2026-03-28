from __future__ import annotations

from pathlib import Path
import os
from typing import Iterable


def load_env_file(path: str | Path = ".env") -> None:
    """Load key=value pairs into os.environ without overwriting existing keys."""
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def load_first_env_file(paths: Iterable[str | Path]) -> Path | None:
    """Load the first existing env file from paths and return that path."""
    for path in paths:
        env_path = Path(path)
        if env_path.exists():
            load_env_file(env_path)
            return env_path
    return None
