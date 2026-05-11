"""跨会话模式挖掘：从 learnings.jsonl 中提取重复模式并生成避坑建议。"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"

Severity = Literal["high", "medium", "low"]


@dataclass
class Pattern:
    key: str
    count: int
    severity: Severity
    recent_takeaways: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""


def mine_patterns(
    min_occurrences: int = 3,
    learnings_path: Optional[Path] = None,
) -> list[Pattern]:
    """从 learnings.jsonl 中提取出现 >= min_occurrences 次的 pattern_key。"""
    fpath = learnings_path or _MEMORY_DIR / "learnings.jsonl"
    if not fpath.exists():
        return []

    lines = fpath.read_text(encoding="utf-8").strip().split("\n")
    records = []
    for line in lines:
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not records:
        return []

    groups: dict[str, list[dict]] = {}
    for rec in records:
        pk = rec.get("pattern_key", "")
        if not pk:
            continue
        groups.setdefault(pk, []).append(rec)

    patterns = []
    for key, recs in groups.items():
        if len(recs) < min_occurrences:
            continue
        takeaways = [r.get("takeaway", "") for r in recs[-3:] if r.get("takeaway")]
        timestamps = [r.get("ts", "") for r in recs if r.get("ts")]
        patterns.append(Pattern(
            key=key,
            count=len(recs),
            severity=_classify_severity(key),
            recent_takeaways=takeaways,
            first_seen=min(timestamps) if timestamps else "",
            last_seen=max(timestamps) if timestamps else "",
        ))

    patterns.sort(key=lambda p: p.count, reverse=True)
    return patterns


def generate_warnings(patterns: list[Pattern]) -> str:
    """将模式列表转换为可注入 active_context 的警告文本块。"""
    if not patterns:
        return ""

    lines = ["## Pattern Warnings (auto-mined)", ""]
    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    for p in patterns:
        icon = severity_icon.get(p.severity, "⚪")
        lines.append(f"{icon} **{p.key}** — 出现 {p.count} 次 (严重度: {p.severity})")
        for tw in p.recent_takeaways[:2]:
            lines.append(f"   - {tw}")
        lines.append("")

    return "\n".join(lines)


def _classify_severity(pattern_key: str) -> Severity:
    key_lower = pattern_key.lower()
    if "fail" in key_lower or "error" in key_lower or "revert" in key_lower:
        return "high"
    if "pass" in key_lower or "success" in key_lower:
        return "low"
    return "medium"
