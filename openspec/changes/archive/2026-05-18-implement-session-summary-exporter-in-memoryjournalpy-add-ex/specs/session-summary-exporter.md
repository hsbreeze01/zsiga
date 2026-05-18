# Spec: Session Summary Exporter

## ADDED Requirements

### REQ-SE-01: Export Session Summary to JSON File

The system SHALL provide an `export_session` function in `zsiga/memory/journal.py` that writes a structured JSON summary file to `memory/sessions/` for each completed pipeline run (change).

#### Scenario: Export summary after a successful change
- **Given** a change named `"add-health-endpoint"` has completed in project `"stockshark"`
- **And** the change record has phases `[enrich, implement, verify, deliver]` all with `outcome=success`
- **When** `export_session(change_name="add-health-endpoint")` is called
- **Then** a file `memory/sessions/<timestamp>-add-health-endpoint.json` SHALL be created
- **And** the file SHALL contain a JSON object with keys: `session_id`, `change_name`, `project`, `exported_at`, `outcome`, `phases`, `lessons`, `metrics`

#### Scenario: Export summary after a failed change
- **Given** a change named `"crawler-domain-strategy"` has reverted during implement phase
- **And** 2 lessons were recorded with `pattern_key="pipeline.fail.implement"`
- **When** `export_session(change_name="crawler-domain-strategy")` is called
- **Then** the summary file SHALL contain `outcome="fail"` and `lessons` array with 2 entries
- **And** the `phases` array SHALL only contain phases that were actually executed

#### Scenario: Export for non-existent change
- **Given** no change record exists for `"nonexistent-change"`
- **When** `export_session(change_name="nonexistent-change")` is called
- **Then** the function SHALL return `None` without writing a file
- **And** no exception SHALL be raised

### REQ-SE-02: Session Summary JSON Structure

The exported JSON file SHALL follow this structure:

```json
{
  "session_id": "<change_name>-<short_hash>",
  "change_name": "string",
  "project": "string",
  "exported_at": "ISO-8601 timestamp",
  "outcome": "success | fail | reverted | skipped",
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "total_runtime_seconds": 123.4,
  "phases": [
    {
      "phase": "enrich | implement | verify | deliver",
      "outcome": "success | fail",
      "turns_used": 5,
      "seconds_used": 42.3,
      "fix_attempts": 0,
      "llm_calls": 3,
      "tool_calls": 12,
      "prompt_tokens": 5000,
      "completion_tokens": 2000
    }
  ],
  "lessons": [
    {
      "pattern_key": "pipeline.pass.deliver",
      "takeaway": "Success"
    }
  ],
  "metrics": {
    "total_llm_calls": 15,
    "total_tool_calls": 45,
    "total_prompt_tokens": 20000,
    "total_completion_tokens": 8000
  }
}
```

#### Scenario: Verify summary structure completeness
- **Given** a change record with all 4 phases and 3 associated lessons
- **When** the summary is exported
- **Then** the JSON SHALL contain all top-level keys: `session_id`, `change_name`, `project`, `exported_at`, `outcome`, `started_at`, `finished_at`, `total_runtime_seconds`, `phases`, `lessons`, `metrics`
- **And** each phase object SHALL contain: `phase`, `outcome`, `turns_used`, `seconds_used`, `fix_attempts`, `llm_calls`, `tool_calls`, `prompt_tokens`, `completion_tokens`

### REQ-SE-03: Session File Naming Convention

Session files SHALL be named using the pattern `{YYYYMMDD-HHmmss}-{change_name}.json` and stored in `memory/sessions/`.

#### Scenario: File naming for a change exported at a specific time
- **Given** current time is `2026-05-15T14:30:00`
- **And** change name is `"add-health-endpoint"`
- **When** `export_session` writes the file
- **Then** the filename SHALL be `20260515-143000-add-health-endpoint.json`
- **And** the file SHALL be located at `memory/sessions/20260515-143000-add-health-endpoint.json`

### REQ-SE-04: Lessons Inclusion in Session Summary

The exported session SHALL include all lessons recorded during the change's time window, linked by `pattern_key` and time proximity.

#### Scenario: Lessons are included from the change time window
- **Given** change `"fix-greenlet"` started at `T1` and finished at `T2`
- **And** 3 lessons were recorded between `T1` and `T2`
- **When** the session summary is exported
- **Then** the `lessons` array SHALL contain those 3 lessons with their `pattern_key` and `takeaway` fields

#### Scenario: No lessons recorded during change
- **Given** a change completed successfully with no lessons recorded
- **When** the session summary is exported
- **Then** the `lessons` array SHALL be empty `[]`

### REQ-SE-05: Load Session Summaries for Cross-Session Context

The system SHALL provide a `load_sessions` function that reads exported session summaries from `memory/sessions/` for use in cross-session context loading.

#### Scenario: Load recent sessions
- **Given** 5 session files exist in `memory/sessions/`
- **When** `load_sessions(limit=3)` is called
- **Then** the function SHALL return the 3 most recent session summaries as a list of dicts
- **And** the list SHALL be ordered from oldest to newest

#### Scenario: No sessions directory
- **Given** `memory/sessions/` directory does not exist
- **When** `load_sessions()` is called
- **Then** the function SHALL return an empty list `[]`
- **And** no exception SHALL be raised

### REQ-SE-06: Directory Auto-Creation

The `memory/sessions/` directory SHALL be automatically created on first export if it does not exist.

#### Scenario: First export creates directory
- **Given** `memory/sessions/` directory does not exist
- **When** `export_session(change_name="first-change")` is called with a valid change record
- **Then** the directory `memory/sessions/` SHALL be created
- **And** the summary file SHALL be written successfully

### REQ-SE-07: Integration with Pipeline Orchestrator

The pipeline orchestrator SHALL call `export_session` after recording a change, regardless of outcome.

#### Scenario: Export called after successful change
- **Given** the orchestrator completes `_process_change` for `"sync-dic-stock"` with `outcome=success`
- **When** the change is recorded via `record_change`
- **Then** `export_session(change_name="sync-dic-stock")` SHALL also be called

#### Scenario: Export called after failed/reverted change
- **Given** the orchestrator reverts `"system-monitoring-tab"` with `outcome=reverted`
- **When** the change is recorded
- **Then** `export_session(change_name="system-monitoring-tab")` SHALL also be called
