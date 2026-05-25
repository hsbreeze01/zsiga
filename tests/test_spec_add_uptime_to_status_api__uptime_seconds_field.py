"""Tests for uptime_seconds field in _build_status_json (spec: uptime-seconds-field)."""
import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from zsiga.daemon import _build_status_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DAEMON_STATE = _REPO_ROOT / "data" / "daemon_state.json"


def _write_daemon_state(state_dict: dict) -> None:
    """Write a temporary daemon_state.json for testing."""
    _DAEMON_STATE.parent.mkdir(parents=True, exist_ok=True)
    _DAEMON_STATE.write_text(json.dumps(state_dict), encoding="utf-8")


def _remove_daemon_state() -> None:
    """Remove daemon_state.json if it exists."""
    if _DAEMON_STATE.exists():
        _DAEMON_STATE.unlink()


@pytest.fixture(autouse=True)
def _preserve_daemon_state():
    """Save and restore daemon_state.json around every test."""
    original = None
    if _DAEMON_STATE.exists():
        original = _DAEMON_STATE.read_text(encoding="utf-8")
    yield
    if original is not None:
        _DAEMON_STATE.write_text(original, encoding="utf-8")
    elif _DAEMON_STATE.exists():
        _DAEMON_STATE.unlink()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


class TestUptimeSecondsPresentWithValidStartedAt:
    """Scenario: uptime_seconds present with valid started_at."""

    def test_uptime_seconds_is_positive_float(self):
        """When started_at is a valid ISO timestamp, uptime_seconds is a positive float."""
        started = datetime.now().isoformat()
        state = {
            "pid": 1234,
            "state": "running",
            "cycle": 1,
            "started_at": started,
            "last_heartbeat": started,
        }
        _write_daemon_state(state)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())

        uptime = data["daemon"]["uptime_seconds"]
        assert uptime is not None, "uptime_seconds should not be None with valid started_at"
        assert isinstance(uptime, (int, float)), f"uptime_seconds should be numeric, got {type(uptime)}"
        assert uptime >= 0, f"uptime_seconds should be >= 0, got {uptime}"
        # Verify rounded to 1 decimal place
        assert uptime == round(uptime, 1), f"uptime_seconds should be rounded to 1 decimal, got {uptime}"


class TestUptimeSecondsNullWhenStartedAtMissing:
    """Scenario: uptime_seconds is null when started_at is missing."""

    def test_uptime_seconds_null_no_started_at(self):
        """When daemon state has no started_at key, uptime_seconds is null."""
        state = {
            "pid": 1234,
            "state": "running",
            "cycle": 1,
            # intentionally no started_at
            "last_heartbeat": "2025-01-15T10:00:00",
        }
        _write_daemon_state(state)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())

        assert data["daemon"]["uptime_seconds"] is None, (
            "uptime_seconds should be None when started_at is missing"
        )

    def test_uptime_seconds_null_empty_daemon_state(self):
        """When daemon_state.json is empty/absent, uptime_seconds is null."""
        _remove_daemon_state()
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())

        assert data["daemon"]["uptime_seconds"] is None


class TestUptimeSecondsNullWhenStartedAtUnparseable:
    """Scenario: uptime_seconds is null when started_at is unparseable."""

    @pytest.mark.parametrize("bad_value", ["garbage", "", "not-a-date", "2025/06/01 12:00"])
    def test_uptime_seconds_null_for_bad_started_at(self, bad_value):
        """When started_at cannot be parsed, uptime_seconds is null."""
        state = {
            "pid": 1234,
            "state": "running",
            "cycle": 1,
            "started_at": bad_value,
            "last_heartbeat": "2025-01-15T10:00:00",
        }
        _write_daemon_state(state)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())

        assert data["daemon"]["uptime_seconds"] is None, (
            f"uptime_seconds should be None for unparseable started_at={bad_value!r}"
        )


class TestUptimeSecondsIncreasesBetweenCalls:
    """Scenario: uptime_seconds increases between consecutive calls."""

    def test_uptime_seconds_monotonically_increasing(self):
        """Two calls spaced apart produce strictly increasing uptime_seconds values."""
        # Use a started_at in the recent past so uptime is non-trivial
        started = datetime.now().isoformat()
        state = {
            "pid": 1234,
            "state": "running",
            "cycle": 1,
            "started_at": started,
            "last_heartbeat": started,
        }
        _write_daemon_state(state)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            first = json.loads(_build_status_json())
            time.sleep(0.15)
            second = json.loads(_build_status_json())

        u1 = first["daemon"]["uptime_seconds"]
        u2 = second["daemon"]["uptime_seconds"]
        assert u1 is not None and u2 is not None, "Both uptime_seconds values should be non-null"
        assert u2 > u1, f"uptime_seconds should increase: first={u1}, second={u2}"


class TestExistingDaemonFieldsUnchanged:
    """Scenario: existing daemon fields remain unchanged."""

    def test_all_pre_existing_fields_preserved(self):
        """Adding uptime_seconds does not alter existing fields."""
        started = datetime.now().isoformat()
        state = {
            "pid": 9999,
            "state": "running",
            "cycle": 42,
            "current_change": "fix-xxx",
            "current_phase": "implement",
            "current_project": "zsiga",
            "started_at": started,
            "last_heartbeat": "2025-01-15T10:30:00",
        }
        _write_daemon_state(state)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())

        d = data["daemon"]
        # Verify all pre-existing fields keep their values
        assert d["pid"] == 9999
        assert d["state"] == "running"
        assert d["cycle"] == 42
        assert d["current_change"] == "fix-xxx"
        assert d["current_phase"] == "implement"
        assert d["current_project"] == "zsiga"
        assert d["heartbeat"] == "2025-01-15T10:30:00"
        # Verify the new field is present
        assert "uptime_seconds" in d, "uptime_seconds should be present in daemon object"
        assert d["uptime_seconds"] is not None, "uptime_seconds should not be None with valid started_at"


class TestTimezoneAwareStartedAt:
    """Scenario: timezone-aware started_at handled correctly."""

    def test_tz_aware_started_at_returns_positive_float(self):
        """When started_at contains timezone info, uptime_seconds is a correct positive float."""
        from datetime import timezone, timedelta

        # Use a recent timestamp with UTC offset
        aware_ts = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
        assert "+" in aware_ts or "Z" in aware_ts, f"Expected tz info in {aware_ts}"

        state = {
            "pid": 1234,
            "state": "running",
            "cycle": 1,
            "started_at": aware_ts,
            "last_heartbeat": aware_ts,
        }
        _write_daemon_state(state)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            data = json.loads(_build_status_json())

        uptime = data["daemon"]["uptime_seconds"]
        assert uptime is not None, "Should return non-None for valid tz-aware started_at"
        assert isinstance(uptime, (int, float)), f"Expected numeric, got {type(uptime)}"
        assert uptime >= 0, f"Expected non-negative uptime, got {uptime}"
        # Should be roughly 60 seconds, allow generous tolerance
        assert 50 <= uptime <= 120, f"Expected ~60s uptime for 60s-old timestamp, got {uptime}"

    def test_tz_aware_and_naive_produce_similar_results(self):
        """A tz-aware started_at and equivalent naive started_at produce similar uptime values."""
        state_naive = {
            "pid": 1234,
            "state": "running",
            "cycle": 1,
            "started_at": datetime.now().isoformat(),
            "last_heartbeat": "2025-01-15T10:00:00",
        }
        from datetime import timezone

        state_aware = {
            "pid": 1234,
            "state": "running",
            "cycle": 1,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat": "2025-01-15T10:00:00",
        }

        _write_daemon_state(state_naive)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            result_naive = json.loads(_build_status_json())["daemon"]["uptime_seconds"]

        _write_daemon_state(state_aware)
        with patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
            result_aware = json.loads(_build_status_json())["daemon"]["uptime_seconds"]

        assert result_naive is not None and result_aware is not None
        diff = abs(result_naive - result_aware)
        assert diff < 5, f"Naive and aware results differ by {diff}s, expected < 5s"
