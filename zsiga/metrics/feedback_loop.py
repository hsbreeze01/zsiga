"""Feedback Loop metrics computation for the dashboard.

Provides four metric groups:
1. Learnings Health — total, active, top pattern_keys, last write
2. Learning Injection Rate — IMPLEMENT/ENRICH injection rates
3. Auto-Proposal Success Rate — total, success, reverted, stuck, rate
4. Self-Assessment Coverage — total, assessed, coverage, last assessment
"""

import json
from collections import Counter
from pathlib import Path
from typing import Optional

from .db import _get_conn

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_LEARNINGS_PATH = _BASE_DIR / "memory" / "learnings.jsonl"

# Pattern keys considered "noise" — excluded from active count
_NOISE_PATTERNS = frozenset({
    "daemon.cycle_error",
})


def _load_learnings_from_jsonl(
    path: Optional[Path] = None,
) -> list[dict]:
    """Read learnings from memory/learnings.jsonl."""
    p = path or _LEARNINGS_PATH
    if not p.exists():
        return []
    entries = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
    return entries


def compute_learnings_health(
    learnings_path: Optional[Path] = None,
) -> dict:
    """Compute Learnings Health metrics.

    Returns dict with: total, active, top_patterns (top-5 pattern_key by freq),
    last_write (ISO timestamp or ''). Empty state returns
    {total: 0, active: 0, top_patterns: [], last_write: ''}.
    """
    entries = _load_learnings_from_jsonl(learnings_path)
    if not entries:
        return {
            "total": 0,
            "active": 0,
            "top_patterns": [],
            "last_write": "",
        }

    total = len(entries)
    pattern_counter = Counter()
    last_write = ""
    active_count = 0

    for entry in entries:
        pk = entry.get("pattern_key", "")
        ts = entry.get("ts", "")
        pattern_counter[pk] += 1
        if pk not in _NOISE_PATTERNS:
            active_count += 1
        if ts > last_write:
            last_write = ts

    top_patterns = [
        {"pattern_key": pk, "count": cnt}
        for pk, cnt in pattern_counter.most_common(5)
    ]

    return {
        "total": total,
        "active": active_count,
        "top_patterns": top_patterns,
        "last_write": last_write,
    }


def compute_injection_rate(db_path: Optional[Path] = None) -> dict:
    """Compute Learning Injection Rate metrics.

    Returns dict with: implement_rate, enrich_rate, avg_per_session.
    Rates are percentages (0-100). Empty state returns zeros.
    """
    conn = _get_conn(db_path)
    try:
        changes = conn.execute(
            "SELECT * FROM changes ORDER BY id ASC"
        ).fetchall()
    finally:
        conn.close()

    if not changes:
        return {
            "implement_rate": 0,
            "enrich_rate": 0,
            "avg_per_session": 0,
        }

    impl_total = 0
    impl_injected = 0
    enrich_total = 0
    enrich_injected = 0
    total_lessons = 0

    for row in changes:
        row_dict = dict(row)
        phases_json = row_dict.get("phases_json", "[]")
        phases = json.loads(phases_json) if phases_json else []
        lessons_count = row_dict.get("lessons_count", 0)
        total_lessons += lessons_count

        for phase in phases:
            phase_name = phase.get("phase", "")
            if phase_name == "implement":
                impl_total += 1
                if lessons_count > 0:
                    impl_injected += 1
            elif phase_name == "enrich":
                enrich_total += 1
                if lessons_count > 0:
                    enrich_injected += 1

    impl_rate = round(impl_injected / impl_total * 100, 1) if impl_total else 0
    enrich_rate = round(
        enrich_injected / enrich_total * 100, 1
    ) if enrich_total else 0
    avg_per_session = round(
        total_lessons / len(changes), 1
    ) if changes else 0

    return {
        "implement_rate": impl_rate,
        "enrich_rate": enrich_rate,
        "avg_per_session": avg_per_session,
    }


def compute_auto_proposal_rate(db_path: Optional[Path] = None) -> dict:
    """Compute Auto-Proposal Success Rate metrics.

    Returns dict with: total, success, reverted, stuck, success_rate.
    stuck = changes with >= 3 reverted attempts.
    """
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT change_name, outcome FROM changes WHERE change_name LIKE 'auto-%'"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "total": 0,
            "success": 0,
            "reverted": 0,
            "stuck": 0,
            "success_rate": 0,
        }

    # Group by change_name to detect stuck (>=3 fails)
    from collections import defaultdict

    name_outcomes = defaultdict(list)
    for row in rows:
        name_outcomes[row["change_name"]].append(row["outcome"])

    total = len(rows)
    success = sum(1 for r in rows if r["outcome"] == "success")
    reverted = sum(1 for r in rows if r["outcome"] == "reverted")

    stuck = 0
    for outcomes in name_outcomes.values():
        fail_count = sum(
            1 for o in outcomes if o in ("reverted", "fail")
        )
        if fail_count >= 3:
            stuck += 1

    success_rate = round(success / total * 100, 1) if total else 0

    return {
        "total": total,
        "success": success,
        "reverted": reverted,
        "stuck": stuck,
        "success_rate": success_rate,
    }


def compute_self_assessment_coverage(db_path: Optional[Path] = None) -> dict:
    """Compute Self-Assessment Coverage metrics.

    Returns dict with: total_changes, assessed_changes, coverage_pct,
    last_assessment (ISO timestamp or '').
    """
    conn = _get_conn(db_path)
    try:
        total_changes = conn.execute(
            "SELECT COUNT(DISTINCT change_name) FROM changes"
        ).fetchone()[0]

        assessed_changes = conn.execute(
            "SELECT COUNT(DISTINCT change_name) FROM self_assessment"
        ).fetchone()[0]

        last_row = conn.execute(
            "SELECT created_at FROM self_assessment ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        last_assessment = last_row["created_at"] if last_row else ""
    finally:
        conn.close()

    coverage_pct = (
        round(assessed_changes / total_changes * 100, 1)
        if total_changes
        else 0
    )

    return {
        "total_changes": total_changes,
        "assessed_changes": assessed_changes,
        "coverage_pct": coverage_pct,
        "last_assessment": last_assessment,
    }
