"""
Spec tests for unify-api-route-style — route-renaming.md

Tests that canonical /api/<resource> paths (without .json suffix) return 200
with correct JSON payloads, and that the response bodies are structurally
identical to what the old .json routes used to serve.
"""
import io
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler
from unittest.mock import patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# Helper: start _serve_dashboard on a free port, return (port, stop_fn)
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_dashboard_server():
    """Start the dashboard HTTP server on a free port.

    Returns (port, stop_thread) where stop_thread can be joined to shut down.
    """
    from zsiga.daemon import _serve_dashboard

    port = _find_free_port()

    # _serve_dashboard blocks forever; run in a thread
    t = threading.Thread(target=_serve_dashboard, args=(port,), daemon=True)
    t.start()

    # Give the server a moment to bind
    import time
    time.sleep(0.3)
    return port, t


@pytest.fixture(scope="module")
def dashboard():
    """Module-scoped fixture: provides (base_url, stop_thread)."""
    port, thread = _start_dashboard_server()
    yield f"http://127.0.0.1:{port}"
    # Server thread is daemon; it will die with the process


# ---------------------------------------------------------------------------
# Scenario: GET /api/status returns 200 with status payload
# ---------------------------------------------------------------------------

class TestCanonicalStatusRoute:
    def test_get_api_status_returns_200_json(self, dashboard):
        """GET /api/status → 200, Content-Type application/json, keys daemon+queue."""
        resp = httpx.get(f"{dashboard}/api/status", follow_redirects=False)
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")
        data = resp.json()
        assert "daemon" in data
        assert "queue" in data


# ---------------------------------------------------------------------------
# Scenario: GET /api/metrics returns 200 with metrics payload
# ---------------------------------------------------------------------------

class TestCanonicalMetricsRoute:
    def test_get_api_metrics_returns_200_json(self, dashboard):
        """GET /api/metrics → 200, Content-Type application/json, parseable."""
        resp = httpx.get(f"{dashboard}/api/metrics", follow_redirects=False)
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")
        data = resp.json()
        assert isinstance(data, dict)
        assert len(data) > 0


# ---------------------------------------------------------------------------
# Scenario: GET /api/current returns 200 with current payload
# ---------------------------------------------------------------------------

class TestCanonicalCurrentRoute:
    def test_get_api_current_returns_200_json(self, dashboard):
        """GET /api/current → 200, Content-Type application/json, parseable."""
        resp = httpx.get(f"{dashboard}/api/current", follow_redirects=False)
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")
        data = resp.json()
        assert isinstance(data, dict)
        assert len(data) > 0


# ---------------------------------------------------------------------------
# Scenario: Response body identical to old .json route (structural identity)
# ---------------------------------------------------------------------------

class TestResponseBodyIdentity:
    def test_status_body_matches_old_status_json(self, dashboard):
        """The JSON from /api/status is structurally identical to the builder output."""
        resp = httpx.get(f"{dashboard}/api/status", follow_redirects=False)
        from zsiga.daemon import _build_status_json
        expected = json.loads(_build_status_json())
        actual = resp.json()
        assert actual["daemon"].keys() == expected["daemon"].keys()
        assert isinstance(actual["queue"], list) == isinstance(expected["queue"], list)

    def test_metrics_body_matches_old_metrics_json(self, dashboard):
        """The JSON from /api/metrics is structurally identical to the builder output."""
        resp = httpx.get(f"{dashboard}/api/metrics", follow_redirects=False)
        from zsiga.daemon import _build_metrics_json
        expected = json.loads(_build_metrics_json())
        actual = resp.json()
        assert actual.keys() == expected.keys()

    def test_current_body_matches_old_current_json(self, dashboard):
        """The JSON from /api/current is structurally identical to the builder output."""
        resp = httpx.get(f"{dashboard}/api/current", follow_redirects=False)
        from zsiga.daemon import _build_current_json
        expected = json.loads(_build_current_json())
        actual = resp.json()
        assert actual.keys() == expected.keys()


# ---------------------------------------------------------------------------
# Scenario: Existing compliant routes unchanged
# ---------------------------------------------------------------------------

class TestUnchangedRoutes:
    def test_health_endpoint_still_works(self, dashboard):
        """GET /api/health → either 200 or 503 (depends on DB state), not 404."""
        resp = httpx.get(f"{dashboard}/api/health", follow_redirects=False)
        assert resp.status_code in (200, 503)
        assert "application/json" in resp.headers.get("content-type", "")

    def test_proposal_stats_endpoint_still_works(self, dashboard):
        """GET /api/proposal-stats → 200 or 500 (error case), not 404."""
        resp = httpx.get(f"{dashboard}/api/proposal-stats", follow_redirects=False)
        assert resp.status_code in (200, 500)
        assert "application/json" in resp.headers.get("content-type", "")
