# Spec: Verify Failure Diagnosis Report

## ADDED Requirements

### Requirement: Structured verify failure classification

The system SHALL analyze historical verify-phase records from `metrics/changes.jsonl` and `memory/learnings.jsonl` and classify each failure into one of the following categories:

- `lint` — failure caused by ruff or syntax errors
- `test` — failure caused by pytest assertion errors or test infrastructure issues
- `regression` — failure caused by a code change that broke previously passing behavior
- `dependency` — failure caused by missing or incorrect imports/modules
- `other` — failure that does not fit the above categories

#### Scenario: Classifying a lint failure

- **Given** a `metrics/changes.jsonl` entry whose verify result contains a ruff violation message
- **When** the diagnosis module processes the entry
- **Then** the failure SHALL be classified as `lint`

#### Scenario: Classifying a test failure

- **Given** a `metrics/changes.jsonl` entry whose verify result contains a pytest traceback or assertion error
- **When** the diagnosis module processes the entry
- **Then** the failure SHALL be classified as `test`

#### Scenario: Classifying a regression failure

- **Given** a `metrics/changes.jsonl` entry whose verify result indicates a previously passing test now fails after a code change
- **When** the diagnosis module processes the entry
- **Then** the failure SHALL be classified as `regression`

#### Scenario: Classifying a dependency failure

- **Given** a `metrics/changes.jsonl` entry whose verify result contains `ModuleNotFoundError` or `ImportError`
- **When** the diagnosis module processes the entry
- **Then** the failure SHALL be classified as `dependency`

### Requirement: TOP-N failure mode summary

The diagnosis module SHALL produce a ranked summary of failure modes showing the top N categories by frequency, including count and percentage of total verify failures.

#### Scenario: Generating TOP-3 summary from historical data

- **Given** at least 10 verify-failure records exist in `metrics/changes.jsonl`
- **When** the diagnosis summary is requested with N=3
- **Then** the output SHALL contain exactly 3 ranked entries ordered by descending frequency
- **And** each entry SHALL include the category name, count, and percentage of total failures

#### Scenario: Handling insufficient data

- **Given** fewer than 3 distinct failure categories exist in the records
- **When** the diagnosis summary is requested with N=3
- **Then** the output SHALL contain only the categories that exist
- **And** the system SHOULD log a warning about insufficient data
