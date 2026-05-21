# Spec: Feedback Loop API Endpoint

## ADDED Requirements

### Requirement: Feedback metrics in /api/status.json

The existing `_build_status_json()` function in `zsiga/daemon.py` SHALL include a `"feedback_metrics"` key in its JSON response payload, populated by calling `compute_feedback_metrics()`.

#### Scenario: status.json includes feedback_metrics key

- **testable**: true
- **target**: zsiga.daemon._build_status_json
- **Given** the daemon is running and `_build_status_json()` is called
- **When** the response is parsed
- **Then** the JSON payload SHALL contain a top-level `"feedback_metrics"` key whose value is a dict with keys `"learnings_health"`, `"injection_rate"`, `"auto_proposal_success"`, and `"self_assessment_coverage"`

#### Scenario: feedback_metrics present even with empty database

- **testable**: true
- **target**: zsiga.daemon._build_status_json
- **Given** an empty metrics database (no changes, no lessons, no self-assessments)
- **When** `_build_status_json()` is called
- **Then** the `"feedback_metrics"` key SHALL still be present with all default values (not null or missing)

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
