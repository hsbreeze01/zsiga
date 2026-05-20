# Proposal: P2 Intent Accuracy Tracking + Confidence Gate

## Summary

Track intent classification accuracy and add confidence threshold gate.

## Implementation

### 1. Add `intent_accuracy` table to metrics/db.py
```sql
CREATE TABLE IF NOT EXISTS intent_accuracy (
    id INTEGER PRIMARY KEY, change_name TEXT, intent_type TEXT,
    confidence REAL, route_taken TEXT, actual_outcome TEXT,
    intent_accurate INTEGER DEFAULT NULL, reasoning TEXT, created_at TEXT
);
```

### 2. Record intent in orchestrator `_process_change()`
After `classify()`: insert row with intent_type, confidence, route_taken.

### 3. Update with outcome after `_run_phases()`
Set actual_outcome, intent_accurate (True if outcome=success, False if reverted).

### 4. Confidence gate
If confidence < 0.6: dispatch explore sub-agent first, then re-classify.

### 5. compute_intent_accuracy() in collector.py

## Constraints
- Scope: project=zsiga
