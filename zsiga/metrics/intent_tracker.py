"""Intent accuracy tracking: CRUD + accuracy computation for the intent_accuracy table."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .db import _get_conn

_DB_PATH = None  # Use default from db.py


def record_intent_decision(
    change_name: str,
    project: str,
    predicted_intent: str,
    confidence: float,
    classification_source: str = "keyword",
    verbalization: str = "",
    reasoning: str = "",
    db_path: Optional[Path] = None,
) -> int:
    """Insert an intent classification decision row.

    Returns the row ID for later updating.
    """
    conn = _get_conn(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO intent_accuracy
               (change_name, project, predicted_intent, confidence,
                classification_source, verbalization, reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                change_name,
                project,
                predicted_intent,
                confidence,
                classification_source,
                verbalization,
                reasoning,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_intent_outcome(
    change_name: str,
    actual_outcome: str,
    is_correct: bool,
    db_path: Optional[Path] = None,
) -> None:
    """Update an intent_accuracy row with the actual pipeline outcome.

    For source='openspec_override', always sets is_correct=True.
    Idempotent: no-op if no matching row exists.
    """
    conn = _get_conn(db_path)
    try:
        # Find the row for this change_name
        row = conn.execute(
            "SELECT id, classification_source FROM intent_accuracy WHERE change_name = ? ORDER BY id DESC LIMIT 1",
            (change_name,),
        ).fetchone()

        if row is None:
            return  # idempotent no-op

        effective_correct = is_correct
        if row["classification_source"] == "openspec_override":
            effective_correct = True

        conn.execute(
            """UPDATE intent_accuracy
               SET actual_outcome = ?, is_correct = ?, updated_at = ?
               WHERE id = ?""",
            (
                actual_outcome,
                1 if effective_correct else 0,
                datetime.now().isoformat(),
                row["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_intent_reclassification(
    row_id: int,
    reclassified_from: str,
    reclassified_to: str,
    db_path: Optional[Path] = None,
) -> None:
    """Update an intent_accuracy row with reclassification info."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """UPDATE intent_accuracy
               SET reclassified_from = ?, reclassified_to = ?, updated_at = ?
               WHERE id = ?""",
            (
                reclassified_from,
                reclassified_to,
                datetime.now().isoformat(),
                row_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def compute_intent_accuracy(db_path: Optional[Path] = None) -> dict:
    """Compute intent accuracy statistics.

    Returns a dict with:
    - total_classified: count of all records
    - total_resolved: count of records with is_correct IS NOT NULL
    - correct_count: count where is_correct = 1
    - accuracy_pct: correct_count / total_resolved * 100 (rounded to 1 decimal), 0.0 if none
    - by_intent: dict mapping each predicted_intent to its accuracy stats
    - low_confidence_count: count of records where confidence < 0.6
    """
    conn = _get_conn(db_path)
    try:
        # Total classified
        total_classified = conn.execute(
            "SELECT COUNT(*) FROM intent_accuracy"
        ).fetchone()[0]

        # Total resolved (is_correct IS NOT NULL)
        total_resolved = conn.execute(
            "SELECT COUNT(*) FROM intent_accuracy WHERE is_correct IS NOT NULL"
        ).fetchone()[0]

        # Correct count
        correct_count = conn.execute(
            "SELECT COUNT(*) FROM intent_accuracy WHERE is_correct = 1"
        ).fetchone()[0]

        # Low confidence count
        low_confidence_count = conn.execute(
            "SELECT COUNT(*) FROM intent_accuracy WHERE confidence < 0.6"
        ).fetchone()[0]

        # Overall accuracy
        accuracy_pct = round(correct_count / total_resolved * 100, 1) if total_resolved > 0 else 0.0

        # Per-intent breakdown
        by_intent = {}
        intent_rows = conn.execute(
            "SELECT predicted_intent, COUNT(*) as cnt, "
            "SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct, "
            "SUM(CASE WHEN is_correct IS NOT NULL THEN 1 ELSE 0 END) as resolved "
            "FROM intent_accuracy GROUP BY predicted_intent"
        ).fetchall()

        for row in intent_rows:
            intent_type = row["predicted_intent"]
            resolved = row["resolved"]
            correct = row["correct"]
            by_intent[intent_type] = {
                "total": row["cnt"],
                "resolved": resolved,
                "correct": correct,
                "accuracy_pct": round(correct / resolved * 100, 1) if resolved > 0 else 0.0,
            }

        return {
            "total_classified": total_classified,
            "total_resolved": total_resolved,
            "correct_count": correct_count,
            "accuracy_pct": accuracy_pct,
            "by_intent": by_intent,
            "low_confidence_count": low_confidence_count,
        }
    finally:
        conn.close()


def get_rolling_accuracy(window: int = 20, db_path: Optional[Path] = None) -> dict:
    """Get rolling accuracy for the last N resolved records.

    Returns overall accuracy and per-intent accuracy for the rolling window.
    """
    conn = _get_conn(db_path)
    try:
        # Get last N resolved records
        rows = conn.execute(
            "SELECT predicted_intent, is_correct FROM intent_accuracy "
            "WHERE is_correct IS NOT NULL ORDER BY id DESC LIMIT ?",
            (window,),
        ).fetchall()

        if not rows:
            return {"accuracy_pct": 0.0, "by_intent": {}, "total": 0}

        total = len(rows)
        correct = sum(1 for r in rows if r["is_correct"] == 1)
        overall = round(correct / total * 100, 1) if total > 0 else 0.0

        # Per-intent
        by_intent = {}
        intent_counts: dict[str, list[int]] = {}
        for r in rows:
            intent_type = r["predicted_intent"]
            intent_counts.setdefault(intent_type, []).append(r["is_correct"])

        for intent_type, values in intent_counts.items():
            t = len(values)
            c = sum(values)
            by_intent[intent_type] = {
                "accuracy_pct": round(c / t * 100, 1) if t > 0 else 0.0,
                "total": t,
            }

        return {
            "accuracy_pct": overall,
            "by_intent": by_intent,
            "total": total,
        }
    finally:
        conn.close()
