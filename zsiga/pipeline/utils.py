import os
import subprocess
import shutil
import sys
from pathlib import Path

from ..transport import Transport, LocalTransport


def _find_venv_python(target_path: str, transport: Transport = None) -> str | None:
    transport = transport or LocalTransport()
    for candidate in ["venv/bin/python", ".venv/bin/python"]:
        full = f"{target_path}/{candidate}"
        if isinstance(transport, LocalTransport):
            if Path(full).exists():
                return str(full)
        else:
            r = transport.run_shell(f"test -f '{full}' && echo EXISTS", timeout=5)
            if "EXISTS" in r.get("stdout", ""):
                return full
    return None


def _ruff_prefix(target_path: str, transport: Transport = None) -> list[str]:
    if shutil.which("ruff"):
        return ["ruff"]
    venv_python = _find_venv_python(target_path, transport)
    if venv_python:
        return [venv_python, "-m", "ruff"]
    return [sys.executable, "-m", "ruff"]


def _wrap_cmd(cmd: str, target_path: str, transport: Transport = None) -> list[str]:
    parts = cmd.split()
    binary = parts[0]
    if shutil.which(binary):
        return parts
    venv_python = _find_venv_python(target_path, transport)
    if venv_python:
        return [venv_python, "-m"] + parts
    return [sys.executable, "-m"] + parts


def verify_mechanical(target_path: str, test_cmd: str, lint_cmd: str,
                      since_sha: str = None,
                      transport: Transport = None) -> tuple[bool, str]:
    transport = transport or LocalTransport()
    errors = []
    ruff = _ruff_prefix(target_path, transport)

    if since_sha:
        changed = _get_changed_files(target_path, since_sha, transport)
        if changed:
            for cmd in [
                " ".join(ruff + ["format"] + changed),
                " ".join(ruff + ["check", "--fix"] + changed),
                " ".join(ruff + ["check"] + changed),
            ]:
                r = transport.run_shell(cmd, cwd=target_path, timeout=120)
            lint_r = r
        else:
            transport.run_shell(" ".join(ruff + ["format", "."]), cwd=target_path)
            lint_r = transport.run_shell(lint_cmd, cwd=target_path, timeout=120)
    else:
        transport.run_shell(" ".join(ruff + ["format", "."]), cwd=target_path)
        lint_r = transport.run_shell(lint_cmd, cwd=target_path, timeout=120)

    if lint_r["exit_code"] != 0:
        errors.append(f"lint:\n{lint_r['stdout'][:2000]}")

    test_r = transport.run_shell(test_cmd, cwd=target_path, timeout=300)
    if test_r["exit_code"] != 0:
        errors.append(f"tests:\n{test_r['stdout'][-3000:]}")

    passed = len(errors) == 0
    return passed, "\n".join(errors)


def _get_changed_files(target_path: str, since_sha: str,
                       transport: Transport = None) -> list[str]:
    transport = transport or LocalTransport()
    r = transport.run_shell(f"git diff --name-only {since_sha} HEAD", cwd=target_path)
    return [f for f in r["stdout"].strip().split("\n") if f and f.endswith(".py")]


def archive_change(target_path: str, change_name: str,
                   transport: Transport = None):
    transport = transport or LocalTransport()
    changes_dir = f"{target_path}/openspec/changes"
    archive_dir = f"{changes_dir}/archive"

    transport.run_shell(f"mkdir -p '{archive_dir}'")

    from datetime import datetime
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    src = f"{changes_dir}/{change_name}"
    dst = f"{archive_dir}/{date_prefix}-{change_name}"

    r = transport.run_shell(f"test -d '{src}' && echo EXISTS", timeout=5)
    if "EXISTS" not in r.get("stdout", ""):
        return

    transport.run_shell(f"mv '{src}' '{dst}'")
