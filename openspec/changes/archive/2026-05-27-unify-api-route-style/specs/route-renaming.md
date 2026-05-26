# Route Renaming — drop `.json` suffix

## MODIFIED Requirements

### Requirement: Canonical route paths without `.json` suffix

The daemon's HTTP handler SHALL match the following canonical paths
(returning 200 with the same JSON payload as the old `.json` variants):

| Canonical path     | Handler function        |
|--------------------|------------------------|
| `/api/status`      | `_build_status_json()`  |
| `/api/metrics`     | `_build_metrics_json()` |
| `/api/current`     | `_build_current_json()` |

The old paths (`/api/status.json`, `/api/metrics.json`, `/api/current.json`)
MUST NOT serve content directly (200); they SHALL redirect instead (see
`redirect-compat.md`).

Existing compliant routes `/api/health`, `/api/pipeline-status`,
`/api/proposal-stats` SHALL remain unchanged.

#### Scenario: GET /api/status returns 200 with status payload

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/status`
- **Then** the response status is 200
- **And** the `Content-Type` header is `application/json`
- **And** the JSON body contains keys `daemon` and `queue`

#### Scenario: GET /api/metrics returns 200 with metrics payload

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/metrics`
- **Then** the response status is 200
- **And** the `Content-Type` header is `application/json`
- **And** the JSON body is parseable and non-empty

#### Scenario: GET /api/current returns 200 with current payload

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/current`
- **Then** the response status is 200
- **And** the `Content-Type` header is `application/json`
- **And** the JSON body is parseable and non-empty

#### Scenario: Response body identical to old .json route

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/status` and `GET /api/status.json` (which redirects)
- **Then** the final JSON body of both requests SHALL be structurally identical
- **And** this holds for `/api/metrics` vs `/api/metrics.json` and `/api/current` vs `/api/current.json` as well

#### Scenario: Existing compliant routes unchanged

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/health`
- **Then** the response behavior SHALL be identical to the pre-change implementation
- **When** a client sends `GET /api/proposal-stats`
- **Then** the response behavior SHALL be identical to the pre-change implementation
