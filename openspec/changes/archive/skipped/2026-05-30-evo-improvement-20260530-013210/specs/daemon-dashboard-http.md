# daemon-dashboard-http

Delta spec for the dashboard HTTP server in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: _serve_dashboard provides HTTP API endpoints

The system SHALL provide `_serve_dashboard(port)` that starts a
`ThreadingHTTPServer` with a `Handler` class that routes GET requests
to JSON-producing functions. It MUST support at minimum `/api/status.json`,
`/api/metrics.json`, and `/api/current.json`.

#### Scenario: _serve_dashboard responds to /api/status.json

- **testable**: true
- **target**: zsiga/daemon.py::_serve_dashboard
- **Given** the dashboard server is started on a random port
- **When** a GET request is sent to `/api/status.json`
- **Then** the response status code is `200`
- **And** the response `Content-Type` header contains `application/json`

#### Scenario: _serve_dashboard responds to /api/metrics.json

- **testable**: true
- **target**: zsiga/daemon.py::_serve_dashboard
- **Given** the dashboard server is started on a random port
- **When** a GET request is sent to `/api/metrics.json`
- **Then** the response status code is `200`
- **And** the response body parses as JSON

#### Scenario: _serve_dashboard responds to /api/current.json

- **testable**: true
- **target**: zsiga/daemon.py::_serve_dashboard
- **Given** the dashboard server is started on a random port
- **When** a GET request is sent to `/api/current.json`
- **Then** the response status code is `200`
- **And** the response body parses as JSON with `daemon` and `current` keys

#### Scenario: _serve_dashboard returns HTML for dashboard route

- **testable**: false

- **Given** the dashboard HTML file exists at `/tmp/zsiga-dashboard/dashboard.html`
- **When** a GET request is sent to `/`
- **Then** the response status code is `200`
- **And** the response `Content-Type` header contains `text/html`
