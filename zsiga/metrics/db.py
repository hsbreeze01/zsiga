"""sqlite3 persistence layer for zsiga metrics.

Replaces jsonl-based storage with a single sqlite3 database.
All data (changes, journal, lessons, stats snapshots) lives here.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "zsiga.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    change_name     TEXT NOT NULL,
    project         TEXT NOT NULL,
    outcome         TEXT NOT NULL,
    started_at      TEXT DEFAULT '',
    finished_at     TEXT DEFAULT '',
    lessons_count   INTEGER DEFAULT 0,
    phases_json     TEXT DEFAULT '[]',
    created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS journal (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    mood            TEXT NOT NULL DEFAULT 'note',
    author          TEXT NOT NULL DEFAULT '',
    text            TEXT NOT NULL,
    created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS lessons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    pattern_key     TEXT DEFAULT '',
    category        TEXT DEFAULT '',
    text            TEXT NOT NULL,
    created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS stats_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_time   TEXT NOT NULL,
    total_changes   INTEGER DEFAULT 0,
    successful      INTEGER DEFAULT 0,
    failed          INTEGER DEFAULT 0,
    success_pct     REAL DEFAULT 0,
    projects_count  INTEGER DEFAULT 0,
    lessons_count   INTEGER DEFAULT 0,
    snapshot_json   TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS level_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    level_tag       TEXT NOT NULL UNIQUE,
    snapshot_time   TEXT NOT NULL,
    successful      INTEGER DEFAULT 0,
    success_pct     REAL DEFAULT 0,
    total_changes   INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    snapshot_json   TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_changes_name ON changes(change_name);
CREATE INDEX IF NOT EXISTS idx_changes_project ON changes(project);
CREATE INDEX IF NOT EXISTS idx_journal_ts ON journal(ts);
CREATE INDEX IF NOT EXISTS idx_lessons_pattern ON lessons(pattern_key);
"""


def _get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or _DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


# ── Changes ──────────────────────────────────────────────────

def record_change(rec_dict: dict, db_path: Optional[Path] = None):
    """Insert a change record. rec_dict comes from ChangeRecord.to_dict()."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """INSERT INTO changes (change_name, project, outcome, started_at,
               finished_at, lessons_count, phases_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                rec_dict["change_name"],
                rec_dict["project"],
                rec_dict["outcome"],
                rec_dict.get("started_at", ""),
                rec_dict.get("finished_at", "") or datetime.now().isoformat(),
                rec_dict.get("lessons_count", 0),
                json.dumps(rec_dict.get("phases", []), ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def load_all_changes(db_path: Optional[Path] = None) -> list[dict]:
    """Load all change records, oldest first."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM changes ORDER BY id ASC"
        ).fetchall()
        return [_row_to_change(dict(r)) for r in rows]
    finally:
        conn.close()


def _row_to_change(row: dict) -> dict:
    """Convert a DB row dict back to the original rec_dict format."""
    return {
        "change_name": row["change_name"],
        "project": row["project"],
        "outcome": row["outcome"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "lessons_count": row["lessons_count"],
        "phases": json.loads(row["phases_json"]) if row["phases_json"] else [],
    }


# ── Journal ──────────────────────────────────────────────────

def write_journal_entry(text: str, mood: str = "note", author: str = "Sisyphus",
                        ts: Optional[str] = None, db_path: Optional[Path] = None):
    """Insert a journal entry."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO journal (ts, mood, author, text) VALUES (?, ?, ?, ?)",
            (ts or datetime.now().isoformat(), mood, author, text),
        )
        conn.commit()
    finally:
        conn.close()


def load_journal(limit: int = 0, db_path: Optional[Path] = None) -> list[dict]:
    """Load journal entries, oldest first. limit=0 means all."""
    conn = _get_conn(db_path)
    try:
        if limit > 0:
            rows = conn.execute(
                "SELECT * FROM journal ORDER BY id ASC LIMIT -1 OFFSET ?",
                (0,),
            ).fetchall()
            # Get total count, then fetch last N
            count = conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0]
            offset = max(0, count - limit)
            rows = conn.execute(
                "SELECT * FROM journal ORDER BY id ASC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM journal ORDER BY id ASC"
            ).fetchall()
        return [{"ts": r["ts"], "mood": r["mood"], "author": r["author"],
                 "text": r["text"]} for r in rows]
    finally:
        conn.close()


# ── Lessons ──────────────────────────────────────────────────

def record_lesson(text: str, pattern_key: str = "", category: str = "",
                  ts: Optional[str] = None, db_path: Optional[Path] = None):
    """Insert a lesson entry."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
            (ts or datetime.now().isoformat(), pattern_key, category, text),
        )
        conn.commit()
    finally:
        conn.close()


def count_lessons(db_path: Optional[Path] = None) -> int:
    conn = _get_conn(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
    finally:
        conn.close()


# ── Stats Snapshots ──────────────────────────────────────────

def save_stats_snapshot(stats: dict, db_path: Optional[Path] = None):
    """Persist a computed stats snapshot."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """INSERT INTO stats_snapshots
               (snapshot_time, total_changes, successful, failed, success_pct,
                projects_count, lessons_count, snapshot_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                stats.get("last_updated", datetime.now().isoformat()),
                stats.get("total_changes", 0),
                stats.get("successful_changes", 0),
                stats.get("failed_changes", 0),
                stats.get("success_rate_pct", 0),
                stats.get("distinct_projects", 0),
                stats.get("lessons_learned", 0),
                json.dumps(stats, ensure_ascii=False, default=str),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def load_latest_snapshot(db_path: Optional[Path] = None) -> Optional[dict]:
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT snapshot_json FROM stats_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return json.loads(row["snapshot_json"])
        return None
    finally:
        conn.close()


# ── Migration ────────────────────────────────────────────────

def migrate_from_jsonl(base_dir: Optional[Path] = None,
                       db_path: Optional[Path] = None):
    """One-time migration: jsonl files → sqlite3.

    Idempotent: checks if data already exists before inserting.
    """
    base = base_dir or Path(__file__).resolve().parent.parent.parent
    conn = _get_conn(db_path)
    try:
        _migrate_changes(conn, base)
        _migrate_journal(conn, base)
        _migrate_lessons(conn, base)
        conn.commit()
    finally:
        conn.close()


def _migrate_changes(conn: sqlite3.Connection, base: Path):
    changes_file = base / "metrics" / "changes.jsonl"
    if not changes_file.exists():
        return
    existing = conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0]
    if existing > 0:
        return
    lines = changes_file.read_text(encoding="utf-8").strip().split("\n")
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        conn.execute(
            """INSERT INTO changes (change_name, project, outcome, started_at,
               finished_at, lessons_count, phases_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                rec["change_name"],
                rec["project"],
                rec["outcome"],
                rec.get("started_at", ""),
                rec.get("finished_at", ""),
                rec.get("lessons_count", 0),
                json.dumps(rec.get("phases", []), ensure_ascii=False),
            ),
        )


def _migrate_journal(conn: sqlite3.Connection, base: Path):
    journal_file = base / "memory" / "journal.jsonl"
    if not journal_file.exists():
        return
    existing = conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0]
    if existing > 0:
        return
    lines = journal_file.read_text(encoding="utf-8").strip().split("\n")
    for line in lines:
        if not line.strip():
            continue
        entry = json.loads(line)
        conn.execute(
            "INSERT INTO journal (ts, mood, author, text) VALUES (?, ?, ?, ?)",
            (entry["ts"], entry.get("mood", "note"), entry.get("author", ""),
             entry["text"]),
        )


def _migrate_lessons(conn: sqlite3.Connection, base: Path):
    lessons_file = base / "memory" / "learnings.jsonl"
    if not lessons_file.exists():
        return
    existing = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
    if existing > 0:
        return
    lines = lessons_file.read_text(encoding="utf-8").strip().split("\n")
    for line in lines:
        if not line.strip():
            continue
        entry = json.loads(line)
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
            (
                entry.get("ts", ""),
                entry.get("pattern_key", ""),
                entry.get("category", ""),
                entry.get("text", entry.get("lesson", "")),
            ),
        )


# ── Level Snapshots ──────────────────────────────────────────

def save_level_snapshot(level_tag: str, stats: dict, tasks_completed: int = 0,
                        db_path: Optional[Path] = None):
    """Persist the stats snapshot when a level is first achieved.

    Uses INSERT OR IGNORE so the first achievement is permanent.
    """
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """INSERT OR IGNORE INTO level_snapshots
               (level_tag, snapshot_time, successful, success_pct,
                total_changes, tasks_completed, snapshot_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                level_tag,
                stats.get("last_updated", datetime.now().isoformat()),
                stats.get("successful_changes", 0),
                stats.get("success_rate_pct", 0),
                stats.get("total_changes", 0),
                tasks_completed,
                json.dumps(stats, ensure_ascii=False, default=str),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def load_level_snapshot(level_tag: str, db_path: Optional[Path] = None) -> Optional[dict]:
    """Load the snapshot for a specific level. Returns None if not yet achieved."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT snapshot_json, tasks_completed, snapshot_time FROM level_snapshots WHERE level_tag = ?",
            (level_tag,),
        ).fetchone()
        if row:
            data = json.loads(row["snapshot_json"])
            data["_level_tasks_completed"] = row["tasks_completed"]
            data["_level_achieved_at"] = row["snapshot_time"]
            return data
        return None
    finally:
        conn.close()
