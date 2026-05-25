"""
Spec tests for unify-api-route-style — test-coverage.md

Tests that the test file itself has been updated to target canonical paths
and includes redirect test cases. These are meta-tests on the test source.
"""
import ast
from pathlib import Path

import pytest

TEST_FILE = Path(__file__).resolve().parent / "test_dashboard_api.py"


def _read_source() -> str:
    assert TEST_FILE.exists(), f"test_dashboard_api.py not found at {TEST_FILE}"
    return TEST_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Scenario: Updated test targets canonical path — no .json in primary assertions
# ---------------------------------------------------------------------------

class TestCanonicalPathAssertions:
    def test_no_status_json_as_primary_target(self):
        """Source of test_dashboard_api.py shall not request /api/status.json
        as the primary assertion target (redirect tests are fine)."""
        source = _read_source()
        # Count occurrences of /api/status.json — if > 0, they must only be
        # in redirect-related tests
        lines = source.splitlines()
        json_refs = [
            (i, line)
            for i, line in enumerate(lines)
            if "/api/status.json" in line or "/api/metrics.json" in line or "/api/current.json" in line
        ]
        # It's acceptable to have .json references only if they are part of
        # redirect testing. We check that at least /api/status (without .json)
        # is referenced more times than /api/status.json
        status_count = source.count('"/api/status"') + source.count("'/api/status'")
        status_json_count = source.count('"/api/status.json"') + source.count("'/api/status.json'")
        assert status_count > 0, "test_dashboard_api.py must reference '/api/status' at least once"
        assert status_count >= status_json_count, (
            f"Canonical '/api/status' ({status_count} refs) should be >= "
            f"legacy '/api/status.json' ({status_json_count} refs)"
        )

    def test_no_metrics_json_as_primary_target(self):
        source = _read_source()
        metrics_count = source.count('"/api/metrics"') + source.count("'/api/metrics'")
        metrics_json_count = source.count('"/api/metrics.json"') + source.count("'/api/metrics.json'")
        assert metrics_count > 0, "test_dashboard_api.py must reference '/api/metrics' at least once"
        assert metrics_count >= metrics_json_count

    def test_no_current_json_as_primary_target(self):
        source = _read_source()
        current_count = source.count('"/api/current"') + source.count("'/api/current'")
        current_json_count = source.count('"/api/current.json"') + source.count("'/api/current.json'")
        assert current_count > 0, "test_dashboard_api.py must reference '/api/current' at least once"
        assert current_count >= current_json_count


# ---------------------------------------------------------------------------
# Scenario: Redirect test cases exist
# ---------------------------------------------------------------------------

class TestRedirectTestsExist:
    def test_301_assertion_exists(self):
        """test_dashboard_api.py shall contain at least one assertion for 301 status."""
        source = _read_source()
        assert "301" in source, (
            "test_dashboard_api.py must contain an assertion for HTTP 301 status code"
        )

    def test_location_header_assertion_exists(self):
        """test_dashboard_api.py shall contain at least one Location header check."""
        source = _read_source()
        has_location = "Location" in source or "location" in source
        assert has_location, (
            "test_dashboard_api.py must assert on the Location header for redirect tests"
        )
