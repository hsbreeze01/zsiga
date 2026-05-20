# Spec: Intent Accuracy Tracking + Confidence Gate

## ADDED Requirements

### Requirement: Intent Accuracy Persistence

The system SHALL record every intent classification decision to a persistent `intent_accuracy` table
immediately after `classify()` returns, and SHALL update the record with the actual pipeline outcome
once the change processing completes.

#### Scenario: Record intent decision after classification

- Given the orchestrator has classified a proposal's intent via `classify()`
- When the classification result is available (intent_type, confidence, verbalization, reasoning, source)
- Then the system SHALL insert a row into `intent_accuracy` with:
  - `change_name` — the change identifier
  - `project` — the target project name
  - `predicted_intent` — the `IntentType` value (string)
  - `confidence` — the confidence score (float 0.0–1.0)
  - `classification_source` — "llm" | "keyword" | "openspec_override"
  - `verbalization` — the verbalization string
  - `reasoning` — the classification reasoning
  - `actual_outcome` — NULL (not yet known)
  - `actual_intent` — NULL (not yet known)
  - `is_correct` — NULL (not yet known)
  - `created_at` — ISO-8601 timestamp
- And the system SHALL return the row ID for later updating

#### Scenario: Update with actual outcome after pipeline completes

- Given an `intent_accuracy` row exists for a change
- When the orchestrator finishes processing that change (success, reverted, fail, skipped)
- Then the system SHALL update the row with:
  - `actual_outcome` — "success" | "reverted" | "fail" | "skipped"
  - `is_correct` — boolean indicating whether the classification led to a successful outcome
- And for `source="openspec_override"`, the system SHALL always set `is_correct = True`
- And the system MUST NOT fail if the row is missing (idempotent no-op)

#### Scenario: Query intent accuracy rates

- Given the `intent_accuracy` table contains N records with non-NULL `is_correct`
- When `compute_intent_accuracy()` is called
- Then it SHALL return a dict with:
  - `total_classified` — count of all records
  - `total_resolved` — count of records with `is_correct IS NOT NULL`
  - `correct_count` — count where `is_correct = 1`
  - `accuracy_pct` — correct_count / total_resolved × 100 (rounded to 1 decimal)
  - `by_intent` — dict mapping each `predicted_intent` to its accuracy stats
  - `low_confidence_count` — count of records where `confidence < 0.6`

---

### Requirement: Classification Source Tracking

The `classify()` function SHALL report which classification source was used, so that accuracy
can be segmented by source (LLM vs keyword vs openspec override).

#### Scenario: Keyword-based classification reports source

- Given `classify()` falls back to keyword matching (no LLM result or LLM overridden)
- When the keyword path produces the final `Intent`
- Then the returned `Intent.reasoning` field SHALL contain a substring indicating the source
  (e.g., "关键词" for keyword-based, or the reasoning string from LLM for LLM-based)

#### Scenario: OpenSpec override reports source

- Given `classify()` is called with `source="openspec"`
- When the hardcoded IMPLEMENTATION intent is returned
- Then the system SHALL record `classification_source = "openspec_override"`

#### Scenario: LLM-based classification reports source

- Given `classify()` uses the LLM result as the final classification
- When the LLM returns a valid `Intent` that is selected
- Then the system SHALL record `classification_source = "llm"`

---

### Requirement: Confidence Gate

The orchestrator SHALL apply a confidence gate: when `classify()` returns confidence < 0.6
AND the route is `"pipeline"`, the system SHALL run the ENRICH phase first to gather more
context, then re-classify with that enriched context before proceeding.

#### Scenario: High-confidence classification proceeds normally

- Given `classify()` returns confidence >= 0.6
- When the route is `"pipeline"` or `"pipeline_fix"`
- Then the orchestrator SHALL proceed to the pipeline without re-classification

#### Scenario: Low-confidence triggers explore-before-pipeline

- Given `classify()` returns confidence < 0.6
- And the route is `"pipeline"`
- When the orchestrator processes the change
- Then the system SHALL first dispatch an explore sub-agent to gather context
- And then re-classify the proposal with the enriched context
- And if the re-classified intent differs from the original, update the route accordingly
- And record both the original and re-classified intent in the accuracy table

#### Scenario: Low-confidence non-pipeline routes unaffected

- Given `classify()` returns confidence < 0.6
- And the route is NOT `"pipeline"` (e.g., `"dispatch_explore"`, `"dispatch_diagnoser"`)
- When the orchestrator processes the change
- Then the system SHALL proceed normally without the confidence gate
  (the route itself already handles exploration/investigation)

---

### Requirement: Reflector Intent Accuracy Signal

The Reflector's `_scan_metric_degradation()` SHALL check intent accuracy metrics and generate
a `metric_degradation` signal when accuracy drops below acceptable thresholds.

#### Scenario: Low intent accuracy triggers signal

- Given the rolling intent accuracy (last 20 resolved records) is below 60%
- When `_scan_metric_degradation()` runs
- Then it SHALL produce a `metric_degradation` signal with:
  - `metric = "intent_accuracy_pct"`
  - `value` = the current accuracy percentage
  - `priority = "high"` if accuracy < 40%, `"medium"` otherwise

#### Scenario: Single intent type with low accuracy triggers signal

- Given a specific intent type (e.g., "implementation") has accuracy below 50%
  across its last 10 resolved records
- When `_scan_metric_degradation()` runs
- Then it SHALL produce a `metric_degradation` signal with:
  - `metric = "intent_accuracy_{intent_type}_pct"`
  - `value` = the per-intent accuracy percentage

#### Scenario: Healthy accuracy produces no signal

- Given the rolling intent accuracy is 70% or above
- When `_scan_metric_degradation()` runs
- Then it SHALL NOT produce any intent accuracy signal

---

### Requirement: Intent Accuracy in Dashboard Stats

The `compute_stats()` function in the metrics collector SHALL include intent accuracy
statistics in its output.

#### Scenario: Stats include intent accuracy fields

- Given `compute_stats()` is called
- When the intent_accuracy table has resolved records
- Then the returned stats dict SHALL include:
  - `intent_accuracy_pct` — overall accuracy percentage
  - `intent_accuracy_by_type` — per-intent-type accuracy dict
  - `intent_low_confidence_count` — count of low-confidence classifications

#### Scenario: Stats handle empty table gracefully

- Given `compute_stats()` is called with no intent_accuracy records
- When the table is empty
- Then the stats SHALL include `intent_accuracy_pct = 0.0` and empty `intent_accuracy_by_type = {}`
