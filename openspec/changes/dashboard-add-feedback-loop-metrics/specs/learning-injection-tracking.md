# Delta Spec: Learning Injection Event Tracking

## ADDED Requirements

### Requirement: learning_injections Table Schema

The system SHALL ensure a `learning_injections` table exists in `data/zsiga.db` with the following columns:

| Column          | Type    | Constraints             |
|-----------------|---------|-------------------------|
| id              | INTEGER | PRIMARY KEY AUTOINCREMENT |
| change_id       | TEXT    | NOT NULL                |
| phase           | TEXT    | NOT NULL                |
| injected_count  | INTEGER | NOT NULL DEFAULT 0      |
| timestamp       | TEXT    | NOT NULL                |

The table SHALL be created with `CREATE TABLE IF NOT EXISTS` so that repeated calls are idempotent and do not destroy existing data.

#### Scenario: Table creation is idempotent

- **testable**: true
- **target**: zsiga/injection_tracker.py::ensure_injections_table
- **Given** an in-memory SQLite database with no `learning_injections` table
- **When** `ensure_injections_table` is called twice with the same connection
- **Then** no exception is raised, the `learning_injections` table exists with columns `id`, `change_id`, `phase`, `injected_count`, `timestamp`, and any rows inserted between the two calls are still present

---

### Requirement: Record Injection Event

The system SHALL provide a function `record_injection` that writes a single row into the `learning_injections` table. The function SHALL accept `change_id` (str), `phase` (str), `injected_count` (int), and an optional `timestamp` (str, defaulting to current UTC ISO-8601). The function SHALL call `ensure_injections_table` before inserting to guarantee the table exists.

#### Scenario: Record a valid injection event

- **testable**: true
- **target**: zsiga/injection_tracker.py::record_injection
- **Given** an in-memory SQLite database
- **When** `record_injection` is called with `change_id="change-001"`, `phase="IMPLEMENT"`, `injected_count=3`
- **Then** the `learning_injections` table contains exactly one row with `change_id=="change-001"`, `phase=="IMPLEMENT"`, `injected_count==3`, and a non-null `timestamp`

#### Scenario: Record multiple injection events for different phases

- **testable**: true
- **target**: zsiga/injection_tracker.py::record_injection
- **Given** an in-memory SQLite database
- **When** `record_injection` is called with `change_id="change-001"`, `phase="IMPLEMENT"`, `injected_count=3`, then again with `change_id="change-001"`, `phase="ENRICH"`, `injected_count=5`
- **Then** the `learning_injections` table contains exactly 2 rows, one with `phase=="IMPLEMENT"` and one with `phase=="ENRICH"`, both with `change_id=="change-001"`

#### Scenario: Record injection with zero count

- **testable**: true
- **target**: zsiga/injection_tracker.py::record_injection
- **Given** an in-memory SQLite database
- **When** `record_injection` is called with `change_id="change-002"`, `phase="IMPLEMENT"`, `injected_count=0`
- **Then** a row is inserted with `injected_count==0` and no exception is raised

#### Scenario: Record injection with explicit timestamp

- **testable**: true
- **target**: zsiga/injection_tracker.py::record_injection
- **Given** an in-memory SQLite database
- **When** `record_injection` is called with `change_id="change-003"`, `phase="ENRICH"`, `injected_count=1`, `timestamp="2025-06-15T10:30:00"`
- **Then** the inserted row has `timestamp=="2025-06-15T10:30:00"`
