import asyncio
import random
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from ..transport import Transport, LocalTransport


def read_file(path: str, transport: Transport = None) -> str | None:
    """Read a file via transport. Returns content or None if not found."""
    transport = transport or LocalTransport()
    r = transport.run_shell(f"cat '{path}'", timeout=10)
    if r["exit_code"] == 0:
        return r["stdout"]
    return None


def file_exists(path: str, transport: Transport = None) -> bool:
    """Check if a file exists via transport."""
    transport = transport or LocalTransport()
    r = transport.run_shell(f"test -f '{path}' && echo EXISTS", timeout=5)
    return "EXISTS" in r.get("stdout", "")


def dir_exists(path: str, transport: Transport = None) -> bool:
    """Check if a directory exists via transport."""
    transport = transport or LocalTransport()
    r = transport.run_shell(f"test -d '{path}' && echo EXISTS", timeout=5)
    return "EXISTS" in r.get("stdout", "")


def list_files_recursive(base_path: str, pattern: str = "*.md",
                          transport: Transport = None) -> list[str]:
    """List files recursively matching a pattern via transport."""
    transport = transport or LocalTransport()
    r = transport.run_shell(f"find '{base_path}' -name '{pattern}' | sort", timeout=10)
    if r["exit_code"] != 0:
        return []
    return [f for f in r["stdout"].strip().split("\n") if f]


def _find_venv_python(target_path: str, transport: Transport = None) -> str | None:
    transport = transport or LocalTransport()
    for candidate in [".venv/bin/python", "venv/bin/python"]:
        full = f"{target_path}/{candidate}"
        if isinstance(transport, LocalTransport):
            if Path(full).exists():
                return str(full)
        else:
            r = transport.run_shell(f"test -f '{full}' && echo EXISTS", timeout=5)
            if "EXISTS" in r.get("stdout", ""):
                return full
    return None


def resolve_venv_python(target_path: str, project_config=None,
                        transport: Transport = None) -> str | None:
    """Resolve venv python path with priority: config → .venv → venv → None."""
    if project_config is not None and getattr(project_config, "venv_path", None):
        return project_config.venv_path
    return _find_venv_python(target_path, transport)


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


def _get_changed_lines_by_file(target_path: str, since_sha: str,
                               transport: Transport = None) -> dict[str, set[int]]:
    """Get changed line numbers per file from git diff (unified format).

    Returns {filepath: {line_numbers}} for lines added or modified.
    """
    transport = transport or LocalTransport()
    r = transport.run_shell(
        f"git diff -U0 {since_sha} HEAD -- '*.py'; "
        f"git diff -U0 --cached -- '*.py'; "
        f"git diff -U0 -- '*.py'",
        cwd=target_path, timeout=30,
    )
    result = {}
    current_file = None
    for line in (r["stdout"] or "").split("\n"):
        if line.startswith("+++ b/") or line.startswith("+++ /"):
            current_file = line[6:]
            if current_file not in result:
                result[current_file] = set()
        elif line.startswith("@@ ") and current_file:
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2) or "1")
                for n in range(start, start + count):
                    result[current_file].add(n)
    return result


def _filter_lint_to_changed_lines(lint_output: str,
                                  changed_lines: dict[str, set[int]]) -> str:
    """Filter ruff lint output to only include errors on changed lines.

    Ruff format: FILE:LINE:COL: CODE ...
    If the error's FILE+LINE is not in changed_lines, skip it.
    Files not tracked in changed_lines are dropped entirely (not kept).
    """
    if not changed_lines:
        return lint_output
    filtered = []
    for line in lint_output.split("\n"):
        match = re.match(r"(.+\.py):(\d+):\d+: ", line)
        if match:
            filepath = match.group(1)
            lineno = int(match.group(2))
            file_lines = changed_lines.get(filepath)
            # Only keep if the file is tracked AND the error is on a changed line
            if file_lines is not None and lineno in file_lines:
                filtered.append(line)
            # If file_lines is None (file not in diff at all), skip entirely
        elif line.strip():
            filtered.append(line)
    return "\n".join(filtered)


def verify_mechanical(target_path: str, test_cmd: str, lint_cmd: str,
                      since_sha: str = None,
                      transport: Transport = None) -> tuple[bool, str]:
    transport = transport or LocalTransport()
    errors = []
    ruff = _ruff_prefix(target_path, transport)

    if since_sha:
        changed = _get_changed_files(target_path, since_sha, transport)
        changed_lines = _get_changed_lines_by_file(target_path, since_sha, transport)
        if changed:
            transport.run_shell(
                " ".join(ruff + ["check", "--fix"] + changed),
                cwd=target_path, timeout=120,
            )
            lint_r = transport.run_shell(
                " ".join(ruff + ["check"] + changed),
                cwd=target_path, timeout=120,
            )
            if lint_r["exit_code"] != 0:
                filtered = _filter_lint_to_changed_lines(
                    lint_r["stdout"][:2000], changed_lines
                )
                if filtered.strip():
                    errors.append(f"lint:\n{filtered}")

        test_targets = _get_test_targets(target_path, since_sha, changed, transport)
        if test_targets:
            test_cmd_scoped = f"{test_cmd} {' '.join(test_targets)}"
            test_r = transport.run_shell(test_cmd_scoped, cwd=target_path, timeout=300)
            if test_r["exit_code"] != 0:
                errors.append(f"tests:\n{test_r['stdout'][-3000:]}")
    else:
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
    r = transport.run_shell(
        f"git diff --name-only {since_sha} HEAD;"
        f"git diff --name-only --cached;"
        f"git ls-files --others --exclude-standard",
        cwd=target_path,
    )
    files = set()
    for line in r["stdout"].strip().split("\n"):
        f = line.strip()
        if f and f.endswith(".py") and "/site-packages/" not in f:
            files.add(f)
    return sorted(files)


def get_all_changed_files(target_path: str, since_sha: str,
                          transport: Transport = None) -> list[str]:
    """Return changed files since *since_sha*, regardless of extension.

    Like ``_get_changed_files`` but does NOT filter to ``.py`` only — needed
    by the must-modify-files gate, which must also count ``.html``, ``.md``,
    ``.yaml``, etc.
    """
    transport = transport or LocalTransport()
    r = transport.run_shell(
        f"git diff --name-only {since_sha} HEAD;"
        f"git diff --name-only --cached;"
        f"git ls-files --others --exclude-standard",
        cwd=target_path,
    )
    files: set[str] = set()
    for line in r["stdout"].strip().split("\n"):
        f = line.strip()
        if not f:
            continue
        if "/site-packages/" in f or "__pycache__" in f:
            continue
        files.add(f)
    return sorted(files)


def must_modify_coverage(must_files: list[str],
                         changed_files: list[str]) -> tuple[float, list[str]]:
    """Return ``(coverage_ratio, missed_files)``.

    coverage_ratio = |must ∩ changed| / |must|.  Empty must_files → (1.0, []).
    """
    if not must_files:
        return 1.0, []
    changed_set = set(changed_files)
    hit = [m for m in must_files if m in changed_set]
    missed = [m for m in must_files if m not in changed_set]
    return len(hit) / len(must_files), missed


def _get_test_targets(target_path: str, since_sha: str,
                      changed_files: list[str],
                      transport: Transport = None) -> list[str]:
    transport = transport or LocalTransport()
    test_files = set()
    for f in changed_files:
        if f.startswith("tests/") or f.startswith("test_"):
            test_files.add(f)
        else:
            parts = f.rsplit("/", 1)
            basename = parts[-1].replace(".py", "")
            r = transport.run_shell(
                f"find '{target_path}/tests' -name 'test_{basename}.py' -o -name '*_test_{basename}.py' 2>/dev/null | head -5",
                timeout=10,
            )
            for line in r.get("stdout", "").strip().split("\n"):
                if line.strip():
                    rel = line.strip()
                    if rel.startswith(target_path):
                        rel = rel[len(target_path):].lstrip("/")
                    test_files.add(rel)

    if not test_files:
        return []

    r = transport.run_shell(
        f"git diff --name-only {since_sha} HEAD -- 'tests/' 'test_*.py'",
        cwd=target_path, timeout=10,
    )
    for line in r.get("stdout", "").strip().split("\n"):
        if line.strip():
            test_files.add(line.strip())

    return sorted(test_files)


def archive_change(target_path: str, change_name: str,
                   transport: Transport = None, sub_dir: str = ""):
    transport = transport or LocalTransport()
    changes_dir = f"{target_path}/openspec/changes"
    if sub_dir:
        archive_dir = f"{changes_dir}/archive/{sub_dir}"
    else:
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


async def retry_with_backoff(
    fn,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retry_on: tuple = (Exception,),
):
    """Retry an async callable with exponential backoff.

    Args:
        fn: Async callable to invoke.
        max_attempts: Maximum number of invocation attempts.
        base_delay: Base delay in seconds for the first retry.
        max_delay: Maximum delay cap in seconds.
        jitter: If True, randomize delay between base_delay*0.5 and computed delay.
        retry_on: Tuple of exception types that trigger a retry.

    Returns:
        The result of the async callable on success.

    Raises:
        The last exception if all attempts fail, or immediately if the
        exception is not in retry_on.
    """
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await fn()
        except retry_on as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                raw_delay = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    delay = random.uniform(raw_delay * 0.5, raw_delay)
                else:
                    delay = raw_delay
                print(
                    f"[retry] attempt {attempt + 1}/{max_attempts} "
                    f"failed ({type(exc).__name__}), "
                    f"retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)
    raise last_exc


def retry_sync(
    fn,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retry_on: tuple = (Exception,),
):
    """Synchronous counterpart of retry_with_backoff for non-async callables."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                raw_delay = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    delay = random.uniform(raw_delay * 0.5, raw_delay)
                else:
                    delay = raw_delay
                print(
                    f"[retry] attempt {attempt + 1}/{max_attempts} "
                    f"failed ({type(exc).__name__}), "
                    f"retrying in {delay:.2f}s"
                )
                time.sleep(delay)
    raise last_exc


# ---------------------------------------------------------------------------
# Dependency-tracking convenience functions (delegate to pipeline/dependency)
# ---------------------------------------------------------------------------

@dataclass
class ConflictResult:
    """Structured result from cross-change conflict detection."""

    change_count: int                         # total pending changes scanned
    conflicts: list                           # list[ConflictPair] from dependency.py
    has_high_severity: bool                   # True if any .py file overlap


def detect_change_conflicts(target_path: str) -> ConflictResult:
    """Scan pending changes for file-level conflicts.

    Returns a :class:`ConflictResult` with the number of changes scanned,
    conflict pairs, and a flag indicating whether any HIGH-severity
    (``.py`` file) overlap exists.
    """
    from .dependency import ChangeConflictDetector

    changes_dir = f"{target_path}/openspec/changes"
    detector = ChangeConflictDetector()
    changes = detector.scan_changes(changes_dir)
    conflicts = detector.find_overlaps(changes)

    has_high = any(
        any(f.endswith(".py") for f in cp.shared_files)
        for cp in conflicts
    )
    return ConflictResult(
        change_count=len(changes),
        conflicts=conflicts,
        has_high_severity=has_high,
    )


def suggest_merge_order(target_path: str) -> list[str]:
    """Return an ordered list of change IDs representing the recommended
    execution sequence.

    Uses :func:`build_dependency_graph` and topological sort internally.
    """
    from .dependency import ChangeConflictDetector, build_dependency_graph

    changes_dir = f"{target_path}/openspec/changes"
    detector = ChangeConflictDetector()
    changes = detector.scan_changes(changes_dir)
    if not changes:
        return []
    graph = build_dependency_graph(changes)
    return graph.topological_order()


def warn_change_conflicts(target_path: str) -> str | None:
    """Return a human-readable warning string if conflicts exist, or
    ``None`` when no conflicts are detected.
    """
    from .dependency import ChangeConflictDetector, build_dependency_graph

    changes_dir = f"{target_path}/openspec/changes"
    detector = ChangeConflictDetector()
    changes = detector.scan_changes(changes_dir)
    if not changes:
        return None
    graph = build_dependency_graph(changes)
    if not graph.edges:
        return None
    return graph.conflict_report()
