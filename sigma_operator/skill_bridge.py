from __future__ import annotations

import subprocess
from pathlib import Path

from .config import get_settings, ensure_paths


def script_path(script_name: str) -> Path:
    settings = get_settings()
    ensure_paths(settings)
    path = settings.script_dir / script_name
    if not path.exists():
        raise FileNotFoundError(f"Missing upstream Sigma helper: {path}")
    return path


def run_skill_python(script_name: str, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    path = script_path(script_name)
    completed = subprocess.run(
        ["python3", str(path), *args],
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        detail = stderr or stdout or f"exit code {completed.returncode}"
        raise RuntimeError(f"{script_name} failed: {detail}")
    return completed
