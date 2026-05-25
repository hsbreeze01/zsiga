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

ALTER TABLE changes ADD COLUMN steward_verdict TEXT DEFAULT '';
ALTER TABLE changes ADD COLUMN steward_score INTEGER DEFAULT -1;
ALTER TABLE changes ADD COLUMN skip_reason TEXT DEFAULT '';

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

CREATE TABLE IF NOT EXISTS intent_accuracy (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    change_name           TEXT NOT NULL,
    project               TEXT NOT NULL,
    predicted_intent      TEXT NOT NULL,
    confidence            REAL NOT NULL,
    classification_source TEXT NOT NULL DEFAULT 'keyword',
    verbalization         TEXT DEFAULT '',
    reasoning             TEXT DEFAULT '',
    actual_outcome        TEXT DEFAULT '',
    actual_intent         TEXT DEFAULT '',
    is_correct            INTEGER DEFAULT NULL,
    reclassified_from     TEXT DEFAULT '',
    reclassified_to       TEXT DEFAULT '',
    created_at            TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now')),
    updated_at            TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_intent_change ON intent_accuracy(change_name);
CREATE INDEX IF NOT EXISTS idx_intent_predicted ON intent_accuracy(predicted_intent);
CREATE INDEX IF NOT EXISTS idx_intent_source ON intent_accuracy(classification_source);

CREATE TABLE IF NOT EXISTS self_assessment (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    change_name       TEXT NOT NULL,
    task_type         TEXT NOT NULL,
    predicted_tokens  INTEGER DEFAULT 0,
    actual_tokens     INTEGER DEFAULT 0,
    predicted_steps   INTEGER DEFAULT 0,
    actual_steps      INTEGER DEFAULT 0,
    fix_attempts      INTEGER DEFAULT 0,
    outcome           TEXT NOT NULL,
    self_rating       TEXT NOT NULL,
    strengths         TEXT DEFAULT '[]',
    weaknesses        TEXT DEFAULT '[]',
    lessons           TEXT DEFAULT '[]',
    created_at        TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_sa_change ON self_assessment(change_name);
CREATE INDEX IF NOT EXISTS idx_sa_task_type ON self_assessment(task_type);
"""


def _get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or _DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


# ── Changes ──────────────────────────────────────────────────

def record_change(rec_dict: dict, db_path: Optional[Path] = None):
    """Insert a change record. rec_dict comes from ChangeRecord.to_dict()."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """INSERT INTO changes (change_name, project, outcome, started_at,
               finished_at, lessons_count, phases_json,
               steward_verdict, steward_score, skip_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec_dict["change_name"],
                rec_dict["project"],
                rec_dict["outcome"],
                rec_dict.get("started_at", ""),
                rec_dict.get("finished_at", "") or datetime.now().isoformat(),
                rec_dict.get("lessons_count", 0),
                json.dumps(rec_dict.get("phases", []), ensure_ascii=False),
                rec_dict.get("steward_verdict", ""),
                rec_dict.get("steward_score", -1),
                rec_dict.get("skip_reason", ""),
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
        "steward_verdict": row.get("steward_verdict", ""),
        "steward_score": row.get("steward_score", -1),
        "skip_reason": row.get("skip_reason", ""),
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
                entry.get("category", entry.get("error_domain", "")),
                entry.get("text", "") or entry.get("takeaway", "") or entry.get("title", ""),
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


# ── Self-Assessment ──────────────────────────────────────────

def record_self_assessment(row: dict, db_path: Optional[Path] = None):
    """Insert a self-assessment row. row keys match self_assessment columns."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """INSERT INTO self_assessment
               (change_name, task_type, predicted_tokens, actual_tokens,
                predicted_steps, actual_steps, fix_attempts, outcome,
                self_rating, strengths, weaknesses, lessons)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["change_name"],
                row["task_type"],
                row.get("predicted_tokens", 0),
                row.get("actual_tokens", 0),
                row.get("predicted_steps", 0),
                row.get("actual_steps", 0),
                row.get("fix_attempts", 0),
                row["outcome"],
                row["self_rating"],
                json.dumps(row.get("strengths", []), ensure_ascii=False),
                json.dumps(row.get("weaknesses", []), ensure_ascii=False),
                json.dumps(row.get("lessons", []), ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def query_self_assessment_stats(task_type: str, limit: int = 10,
                                db_path: Optional[Path] = None) -> dict:
    """Return aggregated stats for the last N entries of a task type.

    Returns ``{avg_tokens, avg_steps, success_rate, count}`` or
    ``{count: 0}`` when no matching rows exist.
    """
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            """SELECT actual_tokens, actual_steps, outcome
               FROM self_assessment
               WHERE task_type = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (task_type, limit),
        ).fetchall()
        if not rows:
            return {"count": 0}
        total_tokens = sum(r["actual_tokens"] for r in rows)
        total_steps = sum(r["actual_steps"] for r in rows)
        success_count = sum(1 for r in rows if r["outcome"] == "success")
        n = len(rows)
        return {
            "avg_tokens": total_tokens / n,
            "avg_steps": total_steps / n,
            "success_rate": success_count / n,
            "count": n,
        }
    finally:
        conn.close()


def query_recent_ratings(task_type: str, limit: int = 3,
                         db_path: Optional[Path] = None) -> list[str]:
    """Return the most recent self_rating values for a task type."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            """SELECT self_rating
               FROM self_assessment
               WHERE task_type = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (task_type, limit),
        ).fetchall()
        return [r["self_rating"] for r in rows]
    finally:
        conn.close()
