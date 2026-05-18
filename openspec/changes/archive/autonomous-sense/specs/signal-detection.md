# Spec: Autonomous Sense — Signal Detection

## ADDED Requirements

### REQ-SENSE-001: Health Check Signal

The system SHALL periodically check configured HTTP endpoints for each target project.
When an endpoint returns non-200 status or times out, the system SHALL emit a `health_check` signal with severity `HIGH`.

#### Scenario: Service returns 500
- Given endpoint `http://localhost:8087/health` is configured for project `compass`
- When the endpoint returns HTTP 500
- Then a Signal with `type=health_check`, `project=compass`, `severity=HIGH` SHALL be emitted
- And the signal data SHALL contain `url`, `http_status`, and `response_body` (truncated to 500 chars)

#### Scenario: Service unreachable
- Given endpoint `http://localhost:8088/` is configured for project `factory`
- When the connection times out after 10 seconds
- Then a Signal with `type=health_check`, `project=factory`, `severity=HIGH` SHALL be emitted
- And the signal data SHALL contain `url` and `error=timeout`

#### Scenario: All services healthy
- Given all configured endpoints return HTTP 200
- When the health check runs
- Then no Signal SHALL be emitted for health_check

### REQ-SENSE-002: Git Changes Signal

The system SHALL detect new commits in target projects since the last scan.
When new commits are found on the main branch, the system SHALL emit a `git_changes` signal with severity `MEDIUM`.

#### Scenario: New commits detected
- Given the last scan recorded HEAD at commit `abc123`
- When `git log abc123..HEAD` returns 5 new commits
- Then a Signal with `type=git_changes`, severity `MEDIUM` SHALL be emitted
- And the signal data SHALL contain `commit_count=5` and `commit_messages` (last 10)

#### Scenario: No new commits
- Given the last scan recorded HEAD at commit `abc123`
- When `git rev-parse HEAD` returns `abc123`
- Then no Signal SHALL be emitted for git_changes

### REQ-SENSE-003: Log Errors Signal

The system SHALL scan service logs (journalctl) for error patterns.
When error/traceback patterns are found in recent logs, the system SHALL emit a `log_errors` signal with severity `MEDIUM`.

#### Scenario: Traceback in compass logs
- Given `d8q-compass` is in the monitored services list
- When `journalctl -u d8q-compass --since 1h` contains "Traceback" or "ERROR"
- Then a Signal with `type=log_errors`, severity `MEDIUM` SHALL be emitted
- And the signal data SHALL contain `service`, `error_count`, and `sample_errors` (first 3)

#### Scenario: Clean logs
- Given monitored service logs contain no error patterns
- When the log scan runs
- Then no Signal SHALL be emitted for log_errors

### REQ-SENSE-004: Quality Signal

The system SHALL run lint checks on target projects and detect quality regressions.
When new lint errors appear compared to the last scan, the system SHALL emit a `quality` signal with severity `MEDIUM`.

#### Scenario: New lint errors
- Given the last scan recorded 5 lint errors
- When `ruff check .` now reports 12 errors
- Then a Signal with `type=quality`, severity `MEDIUM` SHALL be emitted
- And the signal data SHALL contain `previous_count=5`, `current_count=12`, `new_errors` (list)

#### Scenario: No quality regression
- Given lint error count has not increased
- When the quality check runs
- Then no Signal SHALL be emitted for quality

### REQ-SENSE-005: Recurring Pattern Signal

The system SHALL analyze `learnings.jsonl` for recurring failure patterns.
When a `pattern_key` appears ≥ threshold times (default 3), the system SHALL emit a `patterns` signal with severity `MEDIUM`.

#### Scenario: Recurring pattern detected
- Given `learnings.jsonl` contains 4 entries with `pattern_key=pipeline.fail.verify`
- When the pattern threshold is 3
- Then a Signal with `type=patterns`, severity `MEDIUM` SHALL be emitted
- And the signal data SHALL contain `pattern_key`, `occurrence_count=4`, `sample_contexts`

#### Scenario: No recurring patterns
- Given no `pattern_key` appears more than 2 times
- When the pattern analysis runs
- Then no Signal SHALL be emitted for patterns
