import os
import subprocess
import shutil
import sys
from pathlib import Path


def _find_venv_python(target_path: str) -> str | None:
    tp = Path(target_path)
    for candidate in [
        tp / "venv" / "bin" / "python",
        tp / ".venv" / "bin" / "python",
    ]:
        if candidate.exists():
            return str(candidate)
    return None


def _ruff_prefix(target_path: str) -> list[str]:
    if shutil.which("ruff"):
        return ["ruff"]
    venv_python = _find_venv_python(target_path)
    if venv_python:
        return [venv_python, "-m", "ruff"]
    return [sys.executable, "-m", "ruff"]


def _wrap_cmd(cmd: str, target_path: str) -> list[str]:
    parts = cmd.split()
    binary = parts[0]
    if shutil.which(binary):
        return parts
    venv_python = _find_venv_python(target_path)
    if venv_python:
        return [venv_python, "-m"] + parts
    return [sys.executable, "-m"] + parts


def verify_mechanical(target_path: str, test_cmd: str, lint_cmd: str,
                      since_sha: str = None) -> tuple[bool, str]:
    errors = []
    ruff = _ruff_prefix(target_path)
    env = {**os.environ, "PYTHONPATH": target_path}

    if since_sha:
        changed = _get_changed_files(target_path, since_sha)
        if changed:
            subprocess.run(ruff + ["format"] + changed, cwd=target_path,
                           capture_output=True, env=env)
            subprocess.run(ruff + ["check", "--fix"] + changed, cwd=target_path,
                           capture_output=True, text=True, env=env)
            r = subprocess.run(ruff + ["check"] + changed, cwd=target_path,
                               capture_output=True, text=True, env=env)
        else:
            r = subprocess.run(ruff + ["format", "."], cwd=target_path,
                               capture_output=True, env=env)
            r = subprocess.run(_wrap_cmd(lint_cmd, target_path), cwd=target_path,
                               capture_output=True, text=True, env=env)
    else:
        subprocess.run(ruff + ["format", "."], cwd=target_path,
                       capture_output=True, env=env)
        r = subprocess.run(_wrap_cmd(lint_cmd, target_path), cwd=target_path,
                           capture_output=True, text=True, env=env)

    if r.returncode != 0:
        errors.append(f"lint:\n{r.stdout[:2000]}")

    r = subprocess.run(_wrap_cmd(test_cmd, target_path), cwd=target_path,
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        errors.append(f"tests:\n{r.stdout[-3000:]}")

    passed = len(errors) == 0
    return passed, "\n".join(errors)


def _get_changed_files(target_path: str, since_sha: str) -> list[str]:
    r = subprocess.run(
        ["git", "diff", "--name-only", since_sha, "HEAD"],
        cwd=target_path, capture_output=True, text=True,
    )
    return [f for f in r.stdout.strip().split("\n") if f and f.endswith(".py")]


def archive_change(target_path: str, change_name: str):
    changes_dir = Path(target_path) / "openspec" / "changes"
    archive_dir = changes_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    src = changes_dir / change_name
    if not src.exists():
        return

    from datetime import datetime
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    dst = archive_dir / f"{date_prefix}-{change_name}"

    src.rename(dst)
