"""
Spec tests for unify-api-route-style — redirect-compat.md

Tests that old .json-suffixed paths return HTTP 301 with correct Location
headers pointing to the canonical (no-suffix) paths.
"""
import json
import socket
import threading
import time

import httpx
import pytest


# ---------------------------------------------------------------------------
# Helper: start dashboard server (shared with route-renaming test module)
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def dashboard():
    """Module-scoped fixture: provides base_url for the dashboard server."""
    from zsiga.daemon import _serve_dashboard

    port = _find_free_port()
    t = threading.Thread(target=_serve_dashboard, args=(port,), daemon=True)
    t.start()
    time.sleep(0.3)
    yield f"http://127.0.0.1:{port}"


# ---------------------------------------------------------------------------
# Scenario: GET /api/status.json → 301, Location: /api/status
# ---------------------------------------------------------------------------

class TestStatusJsonRedirect:
    def test_status_json_returns_301(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/status.json", follow_redirects=False)
        assert resp.status_code == 301

    def test_status_json_location_header(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/status.json", follow_redirects=False)
        assert resp.headers["Location"] == "/api/status"


# ---------------------------------------------------------------------------
# Scenario: GET /api/metrics.json → 301, Location: /api/metrics
# ---------------------------------------------------------------------------

class TestMetricsJsonRedirect:
    def test_metrics_json_returns_301(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/metrics.json", follow_redirects=False)
        assert resp.status_code == 301

    def test_metrics_json_location_header(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/metrics.json", follow_redirects=False)
        assert resp.headers["Location"] == "/api/metrics"


# ---------------------------------------------------------------------------
# Scenario: GET /api/current.json → 301, Location: /api/current
# ---------------------------------------------------------------------------

class TestCurrentJsonRedirect:
    def test_current_json_returns_301(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/current.json", follow_redirects=False)
        assert resp.status_code == 301

    def test_current_json_location_header(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/current.json", follow_redirects=False)
        assert resp.headers["Location"] == "/api/current"


# ---------------------------------------------------------------------------
# Cross-check: following the redirect yields the canonical response
# ---------------------------------------------------------------------------

class TestRedirectFollowYieldsCanonical:
    def test_status_json_follow_gives_200(self, dashboard):
        """Following the redirect from /api/status.json yields the same as /api/status."""
        resp = httpx.get(f"{dashboard}/api/status.json", follow_redirects=True)
        assert resp.status_code == 200
        data = resp.json()
        assert "daemon" in data
        assert "queue" in data

    def test_metrics_json_follow_gives_200(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/metrics.json", follow_redirects=True)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_current_json_follow_gives_200(self, dashboard):
        resp = httpx.get(f"{dashboard}/api/current.json", follow_redirects=True)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
