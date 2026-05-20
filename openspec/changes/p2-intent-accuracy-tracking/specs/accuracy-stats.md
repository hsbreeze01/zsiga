# Spec: Intent Accuracy Statistics Integration

## ADDED Requirements

### Requirement: Intent Accuracy in Stats

The metrics collector SHALL include intent accuracy statistics in the
computed stats dictionary returned by `compute_stats()`.

#### Scenario: Stats include intent accuracy section

- **Given** the `compute_stats()` function is called
- **When** intent_accuracy records exist in the database
- **Then** the returned stats dict SHALL include an `intent_accuracy` key containing:
  - `total_classified`: total number of intent records
  - `total_resolved`: number of records with `is_correct` not NULL
  - `correct_count`: number where `is_correct = 1`
  - `accuracy_pct`: correct / resolved * 100, rounded to 1 decimal
  - `by_intent`: per-intent-type breakdown of accuracy
  - `low_confidence_count`: number of records with confidence < 0.6

#### Scenario: No intent records — graceful empty

- **Given** no records exist in `intent_accuracy`
- **When** `compute_stats()` is called
- **Then** the `intent_accuracy` key SHALL contain zeros and empty `by_intent`
- **And** `accuracy_pct` SHALL be `0.0`

### Requirement: Intent Accuracy Snapshot Persistence

Intent accuracy stats SHALL be persisted in the stats snapshot
so the dashboard can display historical accuracy trends.

#### Scenario: Snapshot includes intent accuracy

- **Given** `compute_stats()` completes successfully
- **When** `save_stats_snapshot()` is called with the stats dict
- **Then** the snapshot JSON SHALL include the `intent_accuracy` section
