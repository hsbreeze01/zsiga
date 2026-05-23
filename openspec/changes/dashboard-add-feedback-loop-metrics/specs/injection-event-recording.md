# Spec: Injection Event Recording

## ADDED Requirements

### Requirement: injection_events table schema

The system SHALL create an `injection_events` table in `data/zsiga.db` with the following columns:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `change_name` TEXT NOT NULL
- `phase` TEXT NOT NULL
- `injected_count` INTEGER NOT NULL DEFAULT 0
- `timestamp` TEXT NOT NULL DEFAULT current ISO timestamp

The table SHALL be created via the `_SCHEMA` mechanism in `zsiga/metrics/db.py` alongside existing tables, ensuring it is created on first connection if it does not exist.

#### Scenario: Table is created on first database connection

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/metrics/db.py::_get_conn
- **Given** a new temporary sqlite database file
- **When** `_get_conn(db_path=tmp_db)` is called
- **Then** the `injection_events` table SHALL exist in the database schema

### Requirement: record_injection_event function

The system SHALL provide a function `record_injection_event` in `zsiga/metrics/db.py` that inserts a row into the `injection_events` table.

The function SHALL accept:
- `change_name` (str): the change being processed
- `phase` (str): the pipeline phase (e.g., "implement", "enrich")
- `injected_count` (int): number of learnings injected
- `db_path` (optional Path): for testability

#### Scenario: record_injection_event inserts a row

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/metrics/db.py::record_injection_event
- **Given** a temporary sqlite database with the injection_events table
- **When** `record_injection_event(change_name="test-change", phase="implement", injected_count=5, db_path=tmp_db)` is called
- **Then** querying the injection_events table SHALL return exactly 1 row with matching values

#### Scenario: record_injection_event with zero injected count

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/metrics/db.py::record_injection_event
- **Given** a temporary sqlite database with the injection_events table
- **When** `record_injection_event(change_name="test-change", phase="enrich", injected_count=0, db_path=tmp_db)` is called
- **Then** the inserted row SHALL have `injected_count` == 0

### Requirement: query_injection_events function

The system SHALL provide a function `query_injection_events` in `zsiga/metrics/db.py` that returns injection event statistics grouped by phase.

The function SHALL return a dict with:
- `by_phase` (dict[str, dict]): mapping phase → {"count": int, "total_injected": int}
- `avg_injected` (float): average injected_count across all events; 0.0 when no events

#### Scenario: query_injection_events aggregates by phase

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/metrics/db.py::query_injection_events
- **Given** a temporary database with 3 injection_events: 2 for "implement" (counts 3, 5) and 1 for "enrich" (count 2)
- **When** `query_injection_events(db_path=tmp_db)` is called
- **Then** `by_phase["implement"]["count"]` SHALL be 2, `by_phase["implement"]["total_injected"]` SHALL be 8, `avg_injected` SHALL be approximately 3.33

#### Scenario: query_injection_events returns empty when no events

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/metrics/db.py::query_injection_events
- **Given** a temporary database with injection_events table but no rows
- **When** `query_injection_events(db_path=tmp_db)` is called
- **Then** `by_phase` SHALL be an empty dict and `avg_injected` SHALL be 0.0

