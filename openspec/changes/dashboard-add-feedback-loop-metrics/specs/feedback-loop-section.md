# Spec: Dashboard Feedback Loop Metrics Section

## ADDED Requirements

### Requirement: Feedback Loop Section on Dashboard

The dashboard SHALL display a "Feedback Loop" metrics section showing learning loop health indicators.

#### Scenario: Dashboard renders with feedback loop data

- **Given** the dashboard is generated
- **When** the HTML is produced
- **Then** a section titled "Feedback Loop" SHALL appear between existing metrics and Change History

### Requirement: Learnings Health Card

The dashboard SHALL display a learnings health indicator card.

#### Scenario: Learnings exist

- **Given** `memory/learnings.jsonl` has valid entries
- **When** the dashboard is generated
- **Then** the card SHALL show: total count, active count (excluding noise), top 5 pattern_keys by frequency, and last write timestamp

#### Scenario: No learnings exist

- **Given** `memory/learnings.jsonl` is empty or does not exist
- **When** the dashboard is generated
- **Then** the card SHALL show "No learnings yet"

### Requirement: Learning Injection Rate Card

The dashboard SHALL display a learning injection rate indicator.

#### Scenario: Injection data available

- **Given** the DB has injection event records
- **When** the dashboard is generated
- **Then** the card SHALL show: IMPLEMENT injection rate, ENRICH injection rate, and average learnings injected per session

#### Scenario: No injection data

- **Given** no injection events have been recorded
- **When** the dashboard is generated
- **Then** the card SHALL show "No injection data yet — enable learnings injection first"

### Requirement: Auto-Proposal Success Rate Card

The dashboard SHALL display auto-proposal success rate statistics.

#### Scenario: Auto-proposals exist

- **Given** changes with names starting with `auto-` exist in the DB
- **When** the dashboard is generated
- **Then** the card SHALL show: total count, success count, reverted count, stuck count (≥3 fails), success rate percentage

#### Scenario: No auto-proposals

- **Given** no auto-proposals have been generated
- **When** the dashboard is generated
- **Then** the card SHALL show "No auto-proposals yet"

### Requirement: Self-Assessment Coverage Card

The dashboard SHALL display self-assessment coverage statistics.

#### Scenario: Self-assessments exist

- **Given** the self_assessment table has records
- **When** the dashboard is generated
- **Then** the card SHALL show: total changes, assessed changes, coverage percentage, last assessment timestamp

#### Scenario: No self-assessments

- **Given** the self_assessment table is empty
- **When** the dashboard is generated
- **Then** the card SHALL show "No self-assessments recorded"

## REMOVED Requirements

None.
