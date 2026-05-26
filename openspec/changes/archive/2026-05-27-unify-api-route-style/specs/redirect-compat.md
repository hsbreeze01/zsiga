# Backward-Compatible 301 Redirects

## ADDED Requirements

### Requirement: Old `.json` routes redirect with HTTP 301

For each retired path, the daemon SHALL register a redirect handler that
returns **HTTP 301 (Moved Permanently)** with a `Location` header pointing to
the canonical path without the `.json` suffix.

| Old path               | 301 Location header |
|------------------------|---------------------|
| `/api/status.json`     | `/api/status`       |
| `/api/metrics.json`    | `/api/metrics`      |
| `/api/current.json`    | `/api/current`      |

The redirect SHALL NOT include a JSON response body.

#### Scenario: GET /api/status.json returns 301 to /api/status

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/status.json`
- **Then** the response status is 301
- **And** the `Location` header value is `/api/status`

#### Scenario: GET /api/metrics.json returns 301 to /api/metrics

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/metrics.json`
- **Then** the response status is 301
- **And** the `Location` header value is `/api/metrics`

#### Scenario: GET /api/current.json returns 301 to /api/current

- **testable**: true
- **target**: zsiga/daemon.py::Handler.do_GET

- **Given** the dashboard HTTP server is running on any port
- **When** a client sends `GET /api/current.json`
- **Then** the response status is 301
- **And** the `Location` header value is `/api/current`
