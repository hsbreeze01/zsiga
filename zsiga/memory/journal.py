import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..metrics.db import write_journal_entry as _db_write
from ..metrics.db import load_journal as _db_load
from ..metrics.db import load_all_changes as _db_load_changes

_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"
_SESSIONS_DIR = _MEMORY_DIR / "sessions"


def write_entry(text: str, mood: str = "note", author: str = "Sisyphus"):
    valid_moods = {"praise", "criticism", "milestone", "learned", "note"}
    if mood not in valid_moods:
        mood = "note"

    _db_write(text=text, mood=mood, author=author)

    entry = {
        "ts": datetime.now().isoformat(),
        "mood": mood,
        "author": author,
        "text": text,
    }

    journal_file = _MEMORY_DIR / "journal.jsonl"
    journal_file.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_journal(limit: int = 0) -> list[dict]:
    return _db_load(limit=limit)


# ── Session Summary Export ─────────────────────────────────


def _collect_lessons_for_change(change_name: str) -> list[dict]:
    """Load lessons from learnings.jsonl that mention the change_name in their title."""
    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    if not learnings_file.exists():
        return []

    lessons = []
    with open(learnings_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            title = entry.get("title", "")
            if change_name in title:
                lessons.append({
                    "pattern_key": entry.get("pattern_key", ""),
                    "takeaway": entry.get("takeaway", ""),
                })
    return lessons


def _compute_session_metrics(phases: list[dict]) -> dict:
    """Aggregate metrics from phase records."""
    return {
        "total_llm_calls": sum(p.get("llm_calls", 0) for p in phases),
        "total_tool_calls": sum(p.get("tool_calls", 0) for p in phases),
        "total_prompt_tokens": sum(p.get("prompt_tokens", 0) for p in phases),
        "total_completion_tokens": sum(p.get("completion_tokens", 0) for p in phases),
    }


def export_session(
    change_name: str, db_path: Optional[Path] = None
) -> Optional[str]:
    """Export a session summary JSON file for the given change.

    Returns the file path on success, or None if the change is not found.
    """
    changes = _db_load_changes(db_path=db_path)
    change = None
    for c in changes:
        if c["change_name"] == change_name:
            change = c
            break

    if change is None:
        return None

    phases = change.get("phases", [])
    lessons = _collect_lessons_for_change(change_name)
    metrics = _compute_session_metrics(phases)

    finished_at = change.get("finished_at", "")
    raw = f"{change_name}{finished_at}"
    short_hash = hashlib.sha256(raw.encode()).hexdigest()[:8]
    session_id = f"{change_name}-{short_hash}"

    started_at = change.get("started_at", "")
    total_runtime = sum(p.get("seconds_used", 0) for p in phases)

    summary = {
        "session_id": session_id,
        "change_name": change_name,
        "project": change.get("project", ""),
        "exported_at": datetime.now().isoformat(),
        "outcome": change.get("outcome", ""),
        "started_at": started_at,
        "finished_at": finished_at,
        "total_runtime_seconds": round(total_runtime, 1),
        "phases": [
            {
                "phase": p.get("phase", ""),
                "outcome": p.get("outcome", ""),
                "turns_used": p.get("turns_used", 0),
                "seconds_used": p.get("seconds_used", 0),
                "fix_attempts": p.get("fix_attempts", 0),
                "llm_calls": p.get("llm_calls", 0),
                "tool_calls": p.get("tool_calls", 0),
                "prompt_tokens": p.get("prompt_tokens", 0),
                "completion_tokens": p.get("completion_tokens", 0),
            }
            for p in phases
        ],
        "lessons": lessons,
        "metrics": metrics,
    }

    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{change_name}.json"
    filepath = _SESSIONS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return str(filepath)


def load_sessions(limit: int = 0) -> list[dict]:
    """Load exported session summaries from memory/sessions/.

    Returns a list of session dicts ordered oldest-first.
    If limit > 0, returns only the last N sessions.
    """
    if not _SESSIONS_DIR.exists():
        return []

    files = sorted(_SESSIONS_DIR.glob("*.json"))
    if not files:
        return []

    if limit > 0:
        files = files[-limit:]

    sessions = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    return sessions
