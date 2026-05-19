# Delta Spec: Dashboard Failure Diagnosis Panel

## ADDED Requirements

### Requirement: Failure Diagnosis Panel Rendering

The dashboard generator SHALL render a Failure Diagnosis Panel section, positioned after the Phase Performance section and before the Evolution Roadmap section. The panel SHALL display the most recent 10 changes with `outcome` = `"reverted"` or `"fail"` from `data/changes.json`.

Each failure entry MUST include:

- **Change name** and **project**
- **Failed phase** (enrich / implement / verify / deliver)
- **Error summary**: extracted from `memory/learnings.jsonl` — the latest lesson whose text matches the change name or phase
- **Retry count**: number of times this change was re-attempted (derived from duplicate change names in `data/changes.json`)
- **Duration**: computed from `started_at` and `finished_at`, formatted via `_fmt_seconds`
- **Timestamp**: the `finished_at` value in human-readable format
- **Expandable detail**: a `<details><summary>` block containing the full error context from the matching lesson

When no failures exist, the panel SHALL display a "No recent failures 🎉" message.

#### Scenario: Failures exist in changes.json

- **Given** `data/changes.json` contains 3 entries with `outcome` = `"reverted"` and 1 with `outcome` = `"fail"`
- **And** `memory/learnings.jsonl` contains matching lesson entries for 2 of those changes
- **When** the dashboard HTML is generated
- **Then** the Failure Diagnosis Panel SHALL render 4 failure entries, sorted by `finished_at` descending
- **And** each entry SHALL display the 6 required fields
- **And** entries with matching lessons SHALL include a clickable `<details>` section with the full lesson text
- **And** entries without matching lessons SHALL show "No error context available" in the details block

#### Scenario: No failures recorded

- **Given** `data/changes.json` contains only entries with `outcome` = `"delivered"` or `"success"`
- **When** the dashboard HTML is generated
- **Then** the panel SHALL display "No recent failures 🎉"

#### Scenario: More than 10 failures exist

- **Given** `data/changes.json` contains 15 entries with failure outcomes
- **When** the dashboard HTML is generated
- **Then** the panel SHALL display only the 10 most recent failures
