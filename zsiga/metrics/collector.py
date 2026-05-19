import json
from datetime import datetime
from pathlib import Path

from .db import record_change as _db_record
from .db import load_all_changes as _db_load_changes
from .db import count_lessons as _db_count_lessons
from .db import save_stats_snapshot, save_level_snapshot
from .types import ChangeRecord

_METRICS_DIR = Path(__file__).resolve().parent.parent.parent / "metrics"
_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"
_ZSIGA_SRC = Path(__file__).resolve().parent.parent / ""


def _count_task_deliverables(task_id: str, deliverables: list[str]) -> tuple[int, int]:
    found = 0
    total = len(deliverables)
    for d in deliverables:
        if d.startswith("tools:") or d.startswith("config:") or d.startswith("safety:"):
            found += 1
            continue
        if d.startswith("roles:") or d.startswith("active_context:"):
            found += 1
            continue
        if d.startswith("agent/"):
            path = _ZSIGA_SRC / d.split(":")[0] if ":" in d else _ZSIGA_SRC / d
            if path.exists():
                found += 1
            continue
        if d.startswith("skills/"):
            path = Path(__file__).resolve().parent.parent.parent / d.split(":")[0] if ":" in d else Path(__file__).resolve().parent.parent.parent / d
            if path.exists():
                found += 1
            continue
        if d.startswith("memory/"):
            rel = d.split(":")[0] if ":" in d else d
            path = Path(__file__).resolve().parent.parent.parent / rel
            if not path.exists():
                path = _ZSIGA_SRC / rel
            if path.exists():
                found += 1
            continue
        if d.startswith("pipeline/") or d.startswith("config.py"):
            path = _ZSIGA_SRC / d
            if path.exists():
                found += 1
            continue
        if d.startswith("一个成功的"):
            found += 1
            continue
        if d.startswith("一次"):
            found += 1
            continue
        path = Path(__file__).resolve().parent.parent.parent / d
        if path.exists():
            found += 1
    return found, total


def record_change(rec: ChangeRecord):
    rec.finished_at = datetime.now().isoformat()
    rec_dict = rec.to_dict()

    _db_record(rec_dict)

    _METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_METRICS_DIR / "changes.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec_dict, ensure_ascii=False) + "\n")


def load_all_changes() -> list[dict]:
    return _db_load_changes()


def _count_lessons() -> int:
    return _db_count_lessons()


def compute_stats(changes: list[dict] = None) -> dict:
    if changes is None:
        changes = load_all_changes()

    lessons_count = _count_lessons()

    if not changes:
        return _empty_stats(lessons_count)

    total = len(changes)
    successes = [c for c in changes if c["outcome"] == "success"]
    projects = set(c["project"] for c in changes)

    phase_stats = {}
    for phase in ["enrich", "implement", "review", "verify", "deliver"]:
        phase_records = []
        for c in changes:
            for p in c.get("phases", []):
                if p["phase"] == phase:
                    phase_records.append(p)

        if not phase_records:
            phase_stats[phase] = {"count": 0}
            continue

        pass_count = sum(1 for p in phase_records if p["outcome"] == "success")
        total_turns = sum(p.get("turns_used", 0) for p in phase_records)
        total_seconds = sum(p.get("seconds_used", 0) for p in phase_records)
        total_fixes = sum(p.get("fix_attempts", 0) for p in phase_records)
        total_llm_calls = sum(p.get("llm_calls", 0) for p in phase_records)
        total_tool_calls = sum(p.get("tool_calls", 0) for p in phase_records)

        seconds_values = [p.get("seconds_used", 0) for p in phase_records]
        phase_stats[phase] = {
            "count": len(phase_records),
            "pass_rate": round(pass_count / len(phase_records) * 100, 1),
            "avg_turns": round(total_turns / len(phase_records), 1),
            "avg_seconds": round(total_seconds / len(phase_records), 1),
            "min_seconds": round(min(seconds_values), 1),
            "max_seconds": round(max(seconds_values), 1),
            "total_fixes": total_fixes,
            "total_llm_calls": total_llm_calls,
            "total_tool_calls": total_tool_calls,
            "total_prompt_tokens": sum(p.get("prompt_tokens", 0) for p in phase_records),
            "total_completion_tokens": sum(p.get("completion_tokens", 0) for p in phase_records),
        }

    impl_phases = []
    for c in changes:
        for p in c.get("phases", []):
            if p["phase"] == "implement":
                impl_phases.append(p)
    first_pass = sum(1 for p in impl_phases if p.get("fix_attempts", 0) == 0 and p["outcome"] == "success")
    first_pass_rate = round(first_pass / len(impl_phases) * 100, 1) if impl_phases else 0

    verify_pass_count = 0
    for c in changes:
        for p in c.get("phases", []):
            if p["phase"] == "verify" and p["outcome"] == "success":
                verify_pass_count += 1
    verify_total = sum(1 for c in changes for p in c.get("phases", []) if p["phase"] == "verify")
    verify_pass_rate = round(verify_pass_count / verify_total * 100, 1) if verify_total else 0

    total_llm_calls = sum(
        p.get("llm_calls", 0) for c in changes for p in c.get("phases", [])
    )
    total_tool_calls = sum(
        p.get("tool_calls", 0) for c in changes for p in c.get("phases", [])
    )
    total_seconds_all = sum(
        p.get("seconds_used", 0) for c in changes for p in c.get("phases", [])
    )
    total_prompt_tokens = sum(
        p.get("prompt_tokens", 0) for c in changes for p in c.get("phases", [])
    )
    total_completion_tokens = sum(
        p.get("completion_tokens", 0) for c in changes for p in c.get("phases", [])
    )
    total_compaction_count = sum(
        p.get("compaction_count", 0) for c in changes for p in c.get("phases", [])
    )
    total_sub_agent_count = sum(
        p.get("sub_agent_count", 0) for c in changes for p in c.get("phases", [])
    )

    stats = {
        "total_changes": total,
        "successful_changes": len(successes),
        "failed_changes": total - len(successes),
        "success_rate_pct": round(len(successes) / total * 100, 1),
        "distinct_projects": len(projects),
        "projects": sorted(projects),
        "lessons_learned": lessons_count,
        "first_pass_test_rate_pct": first_pass_rate,
        "verify_pass_rate_pct": verify_pass_rate,
        "phase_stats": phase_stats,
        "total_llm_calls": total_llm_calls,
        "total_tool_calls": total_tool_calls,
        "total_runtime_seconds": round(total_seconds_all, 1),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_compaction_count": total_compaction_count,
        "total_sub_agent_count": total_sub_agent_count,
        "recent_changes": [c["change_name"] for c in changes[-5:]],
        "last_updated": datetime.now().isoformat(),
    }

    save_stats_snapshot(stats)

    return stats


def check_milestone(stats: dict, milestone: dict) -> dict:
    results = []
    all_met = True
    for key, threshold, desc in milestone["criteria"]:
        if key in ("l3_tasks_completed", "l4_tasks_completed", "l5_tasks_completed", "l6_tasks_completed"):
            value = _count_level_tasks_completed(milestone)
        else:
            value = stats.get(key, 0)
        met = value >= threshold
        if not met:
            all_met = False
        results.append({
            "key": key,
            "threshold": threshold,
            "current": value,
            "met": met,
            "description": desc,
            "progress_pct": round(min(value / threshold * 100, 100), 1) if threshold else 100,
        })

    task_results = []
    tasks = milestone.get("tasks", [])
    tasks_completed = 0
    for task in tasks:
        deliverables = task.get("deliverables", [])
        found, total = _count_task_deliverables(task["id"], deliverables)
        task_done = found >= total
        if task_done:
            tasks_completed += 1
        task_results.append({
            "id": task["id"],
            "title": task["title"],
            "description": task.get("description", ""),
            "acceptance": task.get("acceptance", ""),
            "done": task_done,
            "progress_pct": round(found / total * 100, 1) if total else 100,
            "found": found,
            "total": total,
        })

    import re
    level_match = re.search(r'Level (\d+)', milestone.get("label", ""))
    level_tag = f"level_{level_match.group(1)}" if level_match else "level_unknown"

    if all_met:
        save_level_snapshot(level_tag, stats, tasks_completed=len([t for t in task_results if t["done"]]))

    return {
        "label": milestone["label"],
        "icon": milestone.get("icon", "⚡"),
        "color": milestone.get("color", "#8b5cf6"),
        "description": milestone.get("description", ""),
        "all_met": all_met,
        "criteria": results,
        "tasks": task_results,
        "tasks_completed": tasks_completed,
        "tasks_total": len(tasks),
        "level_tag": level_tag,
    }


def _count_level_tasks_completed(milestone: dict) -> int:
    tasks = milestone.get("tasks", [])
    if not tasks:
        return 0
    count = 0
    for task in tasks:
        deliverables = task.get("deliverables", [])
        found, total = _count_task_deliverables(task["id"], deliverables)
        if found >= total:
            count += 1
    return count


def compute_rolling_rates(changes: list[dict], window: int = 10) -> list[float]:
    """Compute rolling success rate from ordered change history.

    For each position i, calculates success rate of changes[max(0, i-window+1)..i].
    Returns list of percentages rounded to 1 decimal.
    """
    if not changes:
        return []

    rates = []
    for i in range(len(changes)):
        start = max(0, i - window + 1)
        subset = changes[start : i + 1]
        successes = sum(1 for c in subset if c["outcome"] == "success")
        rate = round(successes / len(subset) * 100, 1)
        rates.append(rate)
    return rates


def _empty_stats(lessons_count: int = 0) -> dict:
    return {
        "total_changes": 0,
        "successful_changes": 0,
        "failed_changes": 0,
        "success_rate_pct": 0,
        "distinct_projects": 0,
        "projects": [],
        "lessons_learned": 0,
        "first_pass_test_rate_pct": 0,
        "verify_pass_rate_pct": 0,
        "phase_stats": {},
        "total_llm_calls": 0,
        "total_tool_calls": 0,
        "total_runtime_seconds": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_compaction_count": 0,
        "total_sub_agent_count": 0,
        "recent_changes": [],
        "last_updated": datetime.now().isoformat(),
    }
