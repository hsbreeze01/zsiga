# health-check-endpoint.md

## ADDED Requirements

### Requirement: Health check function

The daemon SHALL provide a `_health_check(db_path: str) -> dict` function that
performs a lightweight liveness probe against the SQLite database.

The function MUST:
- Attempt a SQLite connection to `db_path` with a `timeout` of 2 seconds.
- Execute `SELECT COUNT(*) FROM changes` on the connected database.
- Return `{"status": "healthy", "db_records": <int>}` when the query succeeds.
- Return `{"status": "unhealthy", "error": "<message>"}` when the database file
  is missing, the `changes` table does not exist, or any exception is raised.
- Close the SQLite connection in all cases (success or failure).
- The function SHALL NOT mutate any state; it is read-only.

#### Scenario: Healthy database returns healthy status with record count

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table containing 5 rows
- **When** `_health_check(db_path)` is called
- **Then** the return dict contains `"status": "healthy"` and `"db_records": 5`

#### Scenario: Missing database file returns unhealthy status

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** no file exists at `db_path`
- **When** `_health_check(db_path)` is called
- **Then** the return dict contains `"status": "unhealthy"` and a non-empty `"error"` string

#### Scenario: Database without changes table returns unhealthy status

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` that contains tables but NOT a `changes` table
- **When** `_health_check(db_path)` is called
- **Then** the return dict contains `"status": "unhealthy"` and a non-empty `"error"` string

---

### Requirement: Health check HTTP endpoint

The daemon SHALL register a `GET /api/health` route in the existing HTTP handler
(the same `Handler` class inside `_serve_dashboard`).

The endpoint MUST:
- Call `_health_check` with the daemon's database path (obtained from
  `zsiga.metrics.db._DB_PATH`).
- When `_health_check` returns `{"status": "healthy", ...}`, respond with HTTP 200
  and a JSON body that includes `status`, `db_records`, and `timestamp` (ISO 8601).
- When `_health_check` returns `{"status": "unhealthy", ...}`, respond with HTTP 503
  and a JSON body that includes `status` and `error`.
- The `timestamp` field MUST be the current UTC time in ISO 8601 format.

#### Scenario: Healthy response returns HTTP 200 with required fields

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database with a `changes` table containing records
- **When** the health check logic is invoked (via `_health_check`)
- **Then** the result dict has key `"status"` equal to `"healthy"`, key `"db_records"`
  that is an integer ≥ 0

#### Scenario: Unhealthy response includes error description

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a path to a non-existent database file
- **When** `_health_check(db_path)` is called
- **Then** the result dict has key `"status"` equal to `"unhealthy"` and key `"error"`
  that is a non-empty string

#### Scenario: Existing endpoints remain functional after adding health check

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon module is imported with the new health check code
- **When** `_build_status_json()` is called
- **Then** it returns valid JSON with `"daemon"` and `"queue"` keys (unchanged behavior)
