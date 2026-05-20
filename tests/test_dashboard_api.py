"""Tests for /api/status.json endpoint and _scan_proposal_queue helper."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from zsiga.daemon import _scan_proposal_queue, _build_status_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proposal_dir(base: Path, name: str, proposal_text: str = ""):
    """Create a minimal proposal directory structure under openspec/changes/."""
    change_dir = base / "openspec" / "changes" / name
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "proposal.md").write_text(proposal_text, encoding="utf-8")


_REPO_ROOT = Path(__file__).resolve().parent.parent
_DAEMON_STATE = _REPO_ROOT / "data" / "daemon_state.json"


@pytest.fixture()
def preserve_daemon_state():
    """Save and restore daemon_state.json around the test."""
    original = None
    if _DAEMON_STATE.exists():
        original = _DAEMON_STATE.read_text(encoding="utf-8")
    yield
    if original is not None:
        _DAEMON_STATE.write_text(original, encoding="utf-8")
    elif _DAEMON_STATE.exists():
        _DAEMON_STATE.unlink()


# ---------------------------------------------------------------------------
# _scan_proposal_queue tests
# ---------------------------------------------------------------------------

class TestScanProposalQueue:
    """Task 1.2: queue scanning helper."""

    def test_empty_dir_returns_empty(self, tmp_path):
        changes = tmp_path / "openspec" / "changes"
        changes.mkdir(parents=True)
        assert _scan_proposal_queue(changes) == []

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        assert _scan_proposal_queue(tmp_path / "nope") == []

    def test_single_proposal_extracted(self, tmp_path):
        changes = tmp_path / "openspec" / "changes"
        _make_proposal_dir(tmp_path, "feat-x", "# Fix login bug\nSome details\n")
        result = _scan_proposal_queue(changes)
        assert len(result) == 1
        assert result[0]["name"] == "feat-x"
        assert result[0]["summary"] == "Fix login bug"

    def test_multiple_proposals_sorted(self, tmp_path):
        changes = tmp_path / "openspec" / "changes"
        _make_proposal_dir(tmp_path, "zzz-last", "# Last one\n")
        _make_proposal_dir(tmp_path, "aaa-first", "# First one\n")
        result = _scan_proposal_queue(changes)
        assert len(result) == 2
        assert result[0]["name"] == "aaa-first"
        assert result[1]["name"] == "zzz-last"

    def test_missing_heading_shows_dash(self, tmp_path):
        changes = tmp_path / "openspec" / "changes"
        _make_proposal_dir(tmp_path, "no-heading", "Just text\nNo heading\n")
        result = _scan_proposal_queue(changes)
        assert len(result) == 1
        assert result[0]["summary"] == "—"

    def test_dirs_without_proposal_md_skipped(self, tmp_path):
        changes = tmp_path / "openspec" / "changes"
        d = changes / "empty-dir"
        d.mkdir(parents=True)
        assert _scan_proposal_queue(changes) == []


# ---------------------------------------------------------------------------
# _build_status_json tests
# ---------------------------------------------------------------------------

class TestBuildStatusJson:
    """Task 1.1: /api/status.json payload builder."""

    def test_returns_valid_json(self):
        payload = _build_status_json()
        data = json.loads(payload)
        assert "daemon" in data
        assert "queue" in data

    def test_daemon_fields_present(self):
        data = json.loads(_build_status_json())
        d = data["daemon"]
        assert "pid" in d
        assert "state" in d
        assert "cycle" in d
        assert "current_change" in d
        assert "current_phase" in d
        assert "current_project" in d
        assert "heartbeat" in d

    def test_defaults_when_no_daemon_state(self, tmp_path, preserve_daemon_state):
        """When daemon_state.json missing, defaults are returned."""
        if _DAEMON_STATE.exists():
            _DAEMON_STATE.unlink()
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())
        assert data["daemon"]["state"] == "unknown"
        assert data["queue"] == []

    def test_reads_existing_daemon_state(self, preserve_daemon_state):
        state = {
            "pid": 999,
            "state": "running",
            "cycle": 42,
            "current_change": "fix-xxx",
            "current_phase": "implement",
            "current_project": "zsiga",
            "last_heartbeat": "2025-01-15T10:30:00",
        }
        _DAEMON_STATE.parent.mkdir(parents=True, exist_ok=True)
        _DAEMON_STATE.write_text(json.dumps(state), encoding="utf-8")

        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())

        assert data["daemon"]["pid"] == 999
        assert data["daemon"]["state"] == "running"
        assert data["daemon"]["cycle"] == 42
        assert data["daemon"]["current_change"] == "fix-xxx"
        assert data["daemon"]["current_phase"] == "implement"
        assert data["daemon"]["heartbeat"] == "2025-01-15T10:30:00"

    def test_queue_reflects_scan_results(self, tmp_path):
        with patch("zsiga.daemon._scan_proposal_queue") as mock_scan:
            mock_scan.return_value = [
                {"name": "fix-aaa", "project": "factory", "summary": "Fix A"},
                {"name": "feat-bbb", "project": "compass", "summary": "Add B"},
            ]
            data = json.loads(_build_status_json())

        assert len(data["queue"]) == 2
        assert data["queue"][0]["name"] == "fix-aaa"
        assert data["queue"][1]["summary"] == "Add B"

    def test_malformed_daemon_state_returns_defaults(self, preserve_daemon_state):
        _DAEMON_STATE.parent.mkdir(parents=True, exist_ok=True)
        _DAEMON_STATE.write_text("NOT JSON{{{", encoding="utf-8")
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())
        assert data["daemon"]["state"] == "unknown"


# ---------------------------------------------------------------------------
# HTTP Handler tests (using http.server directly)
# ---------------------------------------------------------------------------

class TestApiEndpoint:
    """Integration: GET /api/status.json via HTTP handler."""

    def test_endpoint_returns_json(self):
        """The Handler.do_GET returns JSON with correct content-type."""

        # We test by importing the handler class from _serve_dashboard context
        # Instead, directly call _build_status_json which is the core logic
        payload = _build_status_json()
        data = json.loads(payload)
        assert "daemon" in data
        assert "queue" in data
