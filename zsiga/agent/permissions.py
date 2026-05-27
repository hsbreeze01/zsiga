"""Runtime permission profile for agent tool execution."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class PermissionLevel(str, Enum):
    ADVANCED = "advanced"
    STANDARD = "standard"
    STRICT = "strict"


@dataclass
class PermissionConfig:
    level: PermissionLevel = PermissionLevel.STANDARD
    granted_at: str = ""
    overrides: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["level"] = self.level.value
        return data


def permissions_path(base_path: str | Path | None = None) -> Path:
    if base_path is None:
        base_path = os.environ.get(
            "ZSIGA_HOME",
            str(Path(__file__).resolve().parents[2]),
        )
    return Path(base_path) / "data" / "permissions.json"


def load_permissions(base_path: str | Path | None = None) -> PermissionConfig:
    path = permissions_path(base_path)
    if not path.exists():
        return PermissionConfig(
            level=PermissionLevel.STANDARD,
            granted_at=datetime.now().isoformat(),
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        level = PermissionLevel(data.get("level", PermissionLevel.STANDARD.value))
        return PermissionConfig(
            level=level,
            granted_at=data.get("granted_at", ""),
            overrides=data.get("overrides", {}) or {},
        )
    except (OSError, ValueError, TypeError):
        return PermissionConfig(
            level=PermissionLevel.STANDARD,
            granted_at=datetime.now().isoformat(),
        )


def save_permissions(config: PermissionConfig, base_path: str | Path | None = None) -> Path:
    path = permissions_path(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def ensure_permissions(
    base_path: str | Path | None = None,
    reauth: bool = False,
    interactive: bool | None = None,
) -> PermissionConfig:
    """Load or initialize runtime permissions.

    Non-interactive daemon starts default to STANDARD and persist that choice so
    unattended restarts never escalate privileges implicitly.
    """
    path = permissions_path(base_path)
    if path.exists() and not reauth:
        return load_permissions(base_path)

    if interactive is None:
        interactive = sys.stdin.isatty()

    level = PermissionLevel.STANDARD
    if interactive:
        print("zsiga 权限配置：")
        print("  [1] 高级运维 — rsync/scp/systemctl/pip/ssh 全部放行")
        print("  [2] 标准模式 — 只允许 read-only bash + git + pytest/ruff（默认）")
        print("  [3] 严格模式 — bash 完全禁止，仅通过内置工具操作")
        choice = input("选择 [1/2/3] (默认 2): ").strip()
        if choice == "1":
            level = PermissionLevel.ADVANCED
        elif choice == "3":
            level = PermissionLevel.STRICT

    config = PermissionConfig(
        level=level,
        granted_at=datetime.now().isoformat(),
        overrides={
            "allow_commands": [],
            "deny_commands": [],
            "blocked_paths": [],
        },
    )
    save_permissions(config, base_path)
    return config

