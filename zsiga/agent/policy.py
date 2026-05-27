"""Hard policy checks for agent-exposed tools."""

from __future__ import annotations

import fnmatch
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import PurePosixPath

from .permissions import PermissionConfig, PermissionLevel, load_permissions


DEFAULT_PROTECTED_PATHS = [
    "**/.env",
    "**/*secret*",
    "**/*token*",
    "**/*password*",
    "**/*.key",
    "**/*.pem",
]

BLOCKED_COMMAND_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bchmod\s+777\b",
    r"\bgit\s+push\s+--force\b",
    r"\bgit\s+reset\s+--hard\s+origin/(main|master)\b",
]

ADVANCED_ONLY_COMMAND_PATTERNS = [
    r"\bsystemctl\b",
    r"\bsudo\b",
    r"\brsync\b",
    r"\bscp\b",
    r"\bssh\b",
    r"\bpip(?:3)?\s+install\b",
]

STANDARD_ALLOWED_PREFIXES = (
    "cat ",
    "cd ",
    "echo ",
    "find ",
    "git ",
    "grep ",
    "head ",
    "ls ",
    "python ",
    "python3 ",
    "pytest ",
    "pwd",
    "ruff ",
    "sed -n ",
    "tail ",
    "test ",
    "venv/bin/python ",
)

WRITE_COMMAND_PATTERNS = [
    r">\s*(?P<path>[^\s;&|]+)",
    r"\bsed\s+-i(?:\s+\S+)*\s+(?P<path>[^\s;&|]+)",
    r"\bmv\s+\S+\s+(?P<path>[^\s;&|]+)",
    r"\bcp\s+\S+\s+(?P<path>[^\s;&|]+)",
]


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str = ""

    def to_tool_error(self) -> dict:
        return {"error": f"POLICY_DENIED: {self.reason}"}


def normalize_relative_path(target_path: str, path: str) -> str:
    path = path.strip()
    if path.startswith(target_path):
        path = path[len(target_path):].lstrip("/")
    if os.path.isabs(path):
        path = path.lstrip("/")
    normalized = PurePosixPath(path).as_posix()
    while normalized.startswith("../"):
        normalized = normalized[3:]
    return normalized


def _matches(path: str, pattern: str) -> bool:
    path = path.strip("/")
    pattern = pattern.strip("/")
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch("/" + path, pattern)


def check_write_allowed(path: str, protected_paths: list[str] | None = None,
                        allowed_prefix: str | None = None) -> PolicyDecision:
    protected = list(DEFAULT_PROTECTED_PATHS)
    protected.extend(protected_paths or [])
    for pattern in protected:
        if _matches(path, pattern):
            return PolicyDecision(False, f"write to protected path '{path}' matched '{pattern}'")
    if allowed_prefix:
        abs_path = os.path.isabs(path) and path or f"{allowed_prefix}/{path}"
        if not abs_path.startswith(allowed_prefix.rstrip("/") + "/") and abs_path != allowed_prefix.rstrip("/"):
            return PolicyDecision(False,
                f"write outside allowed target '{allowed_prefix}': '{path}'")
    return PolicyDecision(True)


def check_bash_command(
    command: str,
    protected_paths: list[str] | None = None,
    permissions: PermissionConfig | None = None,
    allowed_prefix: str | None = None,
) -> PolicyDecision:
    permissions = permissions or load_permissions()
    stripped = command.strip()
    if permissions.level == PermissionLevel.STRICT:
        return PolicyDecision(False, "bash is disabled in strict permission mode")

    deny_patterns = list(BLOCKED_COMMAND_PATTERNS)
    deny_patterns.extend(permissions.overrides.get("deny_commands", []) or [])
    for pattern in deny_patterns:
        if re.search(pattern, stripped, re.IGNORECASE):
            return PolicyDecision(False, f"blocked command pattern '{pattern}'")

    if permissions.level != PermissionLevel.ADVANCED:
        for pattern in ADVANCED_ONLY_COMMAND_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                return PolicyDecision(False, f"command requires advanced permission: '{pattern}'")

    for path in extract_write_paths(stripped):
        decision = check_write_allowed(path, protected_paths, allowed_prefix)
        if not decision.allowed:
            return decision

    if permissions.level == PermissionLevel.STANDARD and not _looks_standard_allowed(stripped):
        return PolicyDecision(False, "command is outside standard bash allowlist")

    return PolicyDecision(True)


def extract_write_paths(command: str) -> list[str]:
    paths: list[str] = []
    for pattern in WRITE_COMMAND_PATTERNS:
        for match in re.finditer(pattern, command):
            raw = match.group("path")
            if not raw:
                continue
            try:
                parts = shlex.split(raw)
                raw = parts[0] if parts else raw
            except ValueError:
                raw = raw.strip("'\"")
            paths.append(raw.strip("'\""))
    return paths


def _looks_standard_allowed(command: str) -> bool:
    command = command.strip()
    if not command:
        return True
    parts = [p.strip() for p in re.split(r"\s+&&\s+|\s*;\s*", command) if p.strip()]
    return all(part.startswith(STANDARD_ALLOWED_PREFIXES) for part in parts)

