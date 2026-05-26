# Test Coverage Updates

## MODIFIED Requirements

### Requirement: Existing tests target canonical paths

All pre-existing test cases in `tests/test_dashboard_api.py` that request
`.json`-suffixed paths SHALL be updated to request the new canonical paths.
The assertions on response content MUST remain unchanged.

### Requirement: New test cases verify 301 redirects

`tests/test_dashboard_api.py` SHALL include test cases that verify each old
`.json` path returns HTTP 301 with the correct `Location` header.

#### Scenario: Updated test targets canonical path

- **testable**: true
- **target**: tests/test_dashboard_api.py

- **Given** the test file `tests/test_dashboard_api.py`
- **When** reading its source
- **Then** no test function SHALL make an HTTP request to `/api/status.json`, `/api/metrics.json`, or `/api/current.json` as a primary assertion target
- **And** tests SHALL assert on `/api/status`, `/api/metrics`, `/api/current` instead

#### Scenario: Redirect test cases exist

- **testable**: true
- **target**: tests/test_dashboard_api.py

- **Given** the test file `tests/test_dashboard_api.py`
- **When** reading its source
- **Then** there SHALL be at least one test function that asserts a 301 status code is returned for a `.json`-suffixed path
