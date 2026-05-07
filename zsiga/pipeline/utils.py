import subprocess
from pathlib import Path


def verify_mechanical(target_path: str, test_cmd: str, lint_cmd: str) -> tuple[bool, str]:
    errors = []

    subprocess.run(["ruff", "format", "."], cwd=target_path, capture_output=True)

    r = subprocess.run(lint_cmd.split(), cwd=target_path, capture_output=True, text=True)
    if r.returncode != 0:
        errors.append(f"lint:\n{r.stdout[:2000]}")

    r = subprocess.run(test_cmd.split(), cwd=target_path, capture_output=True, text=True)
    if r.returncode != 0:
        errors.append(f"tests:\n{r.stdout[-3000:]}")

    passed = len(errors) == 0
    return passed, "\n".join(errors)


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
