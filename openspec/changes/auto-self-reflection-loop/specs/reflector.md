# Delta Spec: Self-Reflection Loop

## ADDED Requirements

### Requirement: Signal Scanning

The system SHALL provide a `Reflector` that scans three categories of internal signals after each idle daemon cycle:

1. **Recurring failure patterns** — read from `memory/learnings.jsonl`, mine patterns with `min_occurrences=3`, filter `severity="high"`, and check `openspec/changes/` for existing proposals covering the same pattern key.
2. **Metric degradation** — read current stats and compare against a prior snapshot (`data/stats_snapshot.json`); generate a signal when:
   - `success_rate_pct < 70`
   - `verify_pass_rate_pct < 50`
   - ≥ 3 of the last 10 changes have outcome `BUDGET_EXCEEDED`
   - Any metric has dropped > 10% compared to the snapshot (elevates priority).
3. **Recurring root causes** — read the last 10 `outcome=reverted` changes from `metrics/changes.jsonl`, inspect their `diagnosis.md` files, and group identical `root_cause` values; ≥ 2 occurrences of the same root cause SHALL trigger a signal.

#### Scenario: High-severity recurring failure detected

```
Given memory/learnings.jsonl contains a pattern "pipeline.fail.implement" with severity "high" and occurrence count 6
  And openspec/changes/ does not contain a directory whose name includes "pipeline-fail-implement"
When Reflector.scan_signals() is called
Then the returned list SHALL include a Signal with type="recurring_failure"
  And the Signal.pattern_key SHALL identify the pattern
  And the Signal SHALL carry the occurrence count and up to 3 recent takeaway examples
```

#### Scenario: Metric degradation below threshold

```
Given the current success_rate_pct is 40
When Reflector.scan_signals() is called
Then the returned list SHALL include a Signal with type="metric_degradation" and metric="success_rate"
  And Signal.value SHALL be 40
```

#### Scenario: Budget exceed rate triggers signal

```
Given 4 of the last 10 changes in metrics/changes.jsonl have outcome "BUDGET_EXCEEDED"
When Reflector.scan_signals() is called
Then the returned list SHALL include a Signal with type="metric_degradation" and metric="budget_exceed_rate"
```

#### Scenario: Recurring root cause from rollback diagnosis

```
Given 2 reverted changes in metrics/changes.jsonl have diagnosis.md files with identical root_cause "missing_import_in_template"
When Reflector.scan_signals() is called
Then the returned list SHALL include a Signal with type="recurring_root_cause"
  And Signal.root_cause SHALL be "missing_import_in_template"
  And Signal.occurrences SHALL be 2
```

#### Scenario: No signals when everything is healthy

```
Given no high-severity patterns exist in learnings
  And all metrics are above thresholds
  And no reverted changes share a root cause
When Reflector.scan_signals() is called
Then the returned list SHALL be empty
```

---

### Requirement: Deduplication and Rate Limiting

The system SHALL prevent redundant self-reflection proposals:

1. **Dedup** — each generated proposal SHALL be recorded in `data/reflector_history.jsonl` with `timestamp`, `signal_type`, and `pattern_key`. A proposal with the same `signal_type + pattern_key` SHALL NOT be generated within 24 hours.
2. **Rate limit** — at most 3 self-reflection proposals SHALL be generated in any rolling 24-hour window. If `reflector_history.jsonl` contains ≥ 3 entries in the past 24 hours, no new proposals SHALL be generated.
3. **Non-interference** — if `openspec/changes/` already contains a non-`auto-` prefixed proposal (i.e., an external proposal), the Reflector SHALL NOT overwrite or preempt it. The Reflector only runs when there are no pending external proposals.

#### Scenario: Duplicate signal suppressed within 24 hours

```
Given reflector_history.jsonl has an entry with signal_type="recurring_failure" and pattern_key="pipeline-fail-implement" recorded 2 hours ago
When Reflector.should_propose() evaluates a new Signal with the same signal_type and pattern_key
Then it SHALL return False
```

#### Scenario: Rate limit enforced

```
Given reflector_history.jsonl has 3 entries within the past 24 hours
When Reflector.should_propose() evaluates any new Signal
Then it SHALL return False
```

#### Scenario: External proposal takes priority

```
Given openspec/changes/ contains a directory "some-feature" that does NOT start with "auto-"
When Reflector.should_propose() evaluates a Signal
Then it SHALL return False
  And the Reflector SHALL skip proposal generation for this cycle
```

#### Scenario: Proposal allowed when conditions are met

```
Given reflector_history.jsonl has 1 entry within the past 24 hours
  And openspec/changes/ contains no non-auto proposals
  And no duplicate signal_type+pattern_key entry exists in the past 24 hours
When Reflector.should_propose() evaluates a Signal
Then it SHALL return True
```

---

### Requirement: Proposal Generation

The system SHALL generate a proposal directory under `openspec/changes/` with the naming format `auto-{signal_type}-{sanitized_key}-{YYYYMMDD}`.

Each proposal directory SHALL contain a `proposal.md` file with the following sections:
- **Summary** — a human-readable description derived from the signal type
- **Motivation** — specific data from the signal (occurrence count, metric value, root cause occurrences)
- **Expected Behavior** — a general improvement direction based on signal type
- **Constraints** — stating this is auto-generated, scoped to `project=zsiga`, and requires `pytest + ruff` to pass

Proposal content SHALL be produced by pure string templating without calling any LLM.

#### Scenario: Proposal file written correctly

```
Given a Signal with type="recurring_failure", pattern_key="pipeline-fail-implement", count=6
When Reflector.generate_proposal() is called
Then a directory "auto-recurring_failure-pipeline-fail-implement-{today}" SHALL be created under openspec/changes/
  And the directory SHALL contain proposal.md
  And proposal.md SHALL contain a Summary section describing the recurring failure
  And proposal.md SHALL contain a Motivation section referencing the pattern_key and count
  And proposal.md SHALL contain a Constraints section mentioning pytest and ruff
```

#### Scenario: Pattern key is sanitized for filesystem safety

```
Given a Signal with pattern_key="some/pattern:with:special|chars"
When Reflector.generate_proposal() is called
Then the directory name SHALL NOT contain "/", ":", or "|" characters
  And only alphanumeric, hyphens, and underscores SHALL be used in the sanitized key
```

---

### Requirement: Daemon Integration

The daemon loop SHALL invoke the Reflector after `run_cycle()` and before `generate_dashboard()`, subject to the following conditions:
- `idle_cycles >= 3` — the daemon has been idle for at least 3 consecutive cycles
- `processed_count == 0` — no change was processed in the current cycle
- The Reflector invocation is wrapped in a try/except so that errors do not crash the daemon

If the Reflector generates ≥ 1 proposals, the daemon SHALL continue to the next cycle immediately (allowing the new proposals to be picked up).

#### Scenario: Reflector triggered during sustained idle

```
Given the daemon has idle_cycles=4 and processed_count=0
When the daemon loop reaches the post-cycle self-reflection point
Then Reflector.run() SHALL be called
  And any generated proposals SHALL be logged
  And the daemon SHALL continue to the next cycle to pick them up
```

#### Scenario: Reflector NOT triggered during active work

```
Given the daemon has idle_cycles=1 or processed_count=1
When the daemon loop reaches the post-cycle self-reflection point
Then Reflector.run() SHALL NOT be called
```

#### Scenario: Reflector error does not crash daemon

```
Given Reflector.run() raises an exception
When the daemon loop catches the exception
Then the daemon SHALL log a warning message
  And the daemon SHALL continue running normally
```
