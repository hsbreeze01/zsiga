"""
Tests for zsiga/daemon.py path utilities, state reading, lock management,
uptime calculation, and JSON builder functions.

Covers 8 uncovered functions:
  _lock_path, _daemon_state_path, _read_daemon_state,
  acquire_lock, release_lock,
  _compute_uptime_seconds, _build_status_json, _build_metrics_json

Spec: openspec/changes/evo-improvement-20260530-085023/specs/daemon-unit-tests.md
"""

import json
import os
from datetime import datetime
from unittest.mock import patch

# ── _lock_path ──────────────────────────────────────────────────────────────


class TestLockPath:
    """_lock_path() resolves to <ZSIGA_HOME>/data/lock.pid."""

    def test_returns_data_lock_pid_under_zsiga_home(self, tmp_path, monkeypatch):
        """Scenario: _lock_path returns data/lock.pid under ZSIGA_HOME"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        from zsiga.daemon import _lock_path

        result = _lock_path()
        assert result == tmp_path / "data" / "lock.pid"

    def test_creates_data_directory_if_missing(self, tmp_path, monkeypatch):
        """Scenario: _lock_path creates data directory if missing"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        assert not (tmp_path / "data").exists()
        from zsiga.daemon import _lock_path

        result = _lock_path()
        assert (tmp_path / "data").is_dir()
        assert str(result).endswith("data/lock.pid")


# ── _daemon_state_path ──────────────────────────────────────────────────────


class TestDaemonStatePath:
    """_daemon_state_path() resolves to <ZSIGA_HOME>/data/daemon_state.json."""

    def test_returns_data_daemon_state_json_under_zsiga_home(
        self, tmp_path, monkeypatch
    ):
        """Scenario: _daemon_state_path returns data/daemon_state.json under ZSIGA_HOME"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        from zsiga.daemon import _daemon_state_path

        result = _daemon_state_path()
        assert result == tmp_path / "data" / "daemon_state.json"


# ── _read_daemon_state ──────────────────────────────────────────────────────


class TestReadDaemonState:
    """_read_daemon_state() parses daemon_state.json or returns {}."""

    @staticmethod
    def _write_state(tmp_path, content: str):
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "daemon_state.json").write_text(content, encoding="utf-8")

    def test_returns_dict_from_valid_json(self, tmp_path, monkeypatch):
        """Scenario: _read_daemon_state returns dict from valid JSON file"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        self._write_state(tmp_path, '{"pid": 123, "state": "running"}')
        from zsiga.daemon import _read_daemon_state

        result = _read_daemon_state()
        assert result == {"pid": 123, "state": "running"}

    def test_returns_empty_dict_when_file_missing(self, tmp_path, monkeypatch):
        """Scenario: _read_daemon_state returns empty dict when file is missing"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        from zsiga.daemon import _read_daemon_state

        result = _read_daemon_state()
        assert result == {}

    def test_returns_empty_dict_for_malformed_json(self, tmp_path, monkeypatch):
        """Scenario: _read_daemon_state returns empty dict for malformed JSON"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        self._write_state(tmp_path, "not-valid-json")
        from zsiga.daemon import _read_daemon_state

        result = _read_daemon_state()
        assert result == {}


# ── acquire_lock / release_lock ─────────────────────────────────────────────


class TestAcquireLock:
    """acquire_lock() uses fcntl to obtain exclusive PID lock."""

    def test_succeeds_when_no_other_lock_held(self, tmp_path, monkeypatch):
        """Scenario: acquire_lock succeeds when no other lock is held"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        from zsiga.daemon import acquire_lock

        fd, ok = acquire_lock()
        try:
            assert ok is True
            assert fd is not None
            lock_path = tmp_path / "data" / "lock.pid"
            pid_in_file = lock_path.read_text().strip()
            assert pid_in_file == str(os.getpid())
        finally:
            fd.close()
            lock_path = tmp_path / "data" / "lock.pid"
            if lock_path.exists():
                lock_path.unlink()

    def test_fails_when_flock_raises_oserror(self, tmp_path, monkeypatch):
        """Scenario: acquire_lock fails when flock raises OSError"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        import builtins

        orig_open = builtins.open

        def _open_plus_r(*args, **kwargs):
            if len(args) >= 2 and args[1] == "w" and "lock.pid" in str(args[0]):
                args = (args[0], "w+") + args[2:]
            return orig_open(*args, **kwargs)

        with patch("zsiga.daemon.fcntl.flock", side_effect=OSError("locked")), \
             patch("builtins.open", side_effect=_open_plus_r):
            from zsiga.daemon import acquire_lock

            fd, ok = acquire_lock()

        assert ok is False
        assert fd is None


class TestReleaseLock:
    """release_lock(fd) closes fd and removes lock file."""

    def test_removes_lock_file(self, tmp_path, monkeypatch):
        """Scenario: release_lock closes fd and removes lock file"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        from zsiga.daemon import acquire_lock, release_lock

        fd, ok = acquire_lock()
        assert ok is True
        lock_path = tmp_path / "data" / "lock.pid"
        assert lock_path.exists()
        release_lock(fd)
        assert not lock_path.exists()

    def test_ignores_file_not_found_error(self, tmp_path, monkeypatch):
        """Scenario: release_lock ignores FileNotFoundError gracefully"""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        from zsiga.daemon import _lock_path, release_lock

        lock_path = _lock_path()
        fd = open(lock_path, "w")  # noqa: SIM115
        fd.write("test")
        fd.flush()
        lock_path.unlink()  # file gone before release

        # Should not raise
        release_lock(fd)


# ── _compute_uptime_seconds ─────────────────────────────────────────────────


class TestComputeUptimeSeconds:
    """_compute_uptime_seconds() computes elapsed seconds from ISO datetime."""

    def test_returns_elapsed_seconds_for_valid_string(self):
        """Scenario: _compute_uptime_seconds returns elapsed seconds for valid ISO string"""
        from zsiga.daemon import _compute_uptime_seconds

        started = "2025-06-15T10:00:00"
        fake_now = datetime(2025, 6, 15, 10, 1, 30)

        with patch("zsiga.daemon.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.fromisoformat = datetime.fromisoformat
            result = _compute_uptime_seconds(started)

        assert result == 90.0

    def test_returns_none_for_none_input(self):
        """Scenario: _compute_uptime_seconds returns None for None input"""
        from zsiga.daemon import _compute_uptime_seconds

        assert _compute_uptime_seconds(None) is None

    def test_returns_none_for_empty_string(self):
        """Scenario: _compute_uptime_seconds returns None for empty string"""
        from zsiga.daemon import _compute_uptime_seconds

        assert _compute_uptime_seconds("") is None

    def test_returns_none_for_unparseable_string(self):
        """Scenario: _compute_uptime_seconds returns None for unparseable string"""
        from zsiga.daemon import _compute_uptime_seconds

        assert _compute_uptime_seconds("not-a-date") is None


# ── _build_status_json ──────────────────────────────────────────────────────


class TestBuildStatusJson:
    """_build_status_json() returns JSON with daemon state."""

    def test_returns_valid_json_with_daemon_key(self):
        """Scenario: _build_status_json returns valid JSON with daemon key"""
        from zsiga.daemon import _build_status_json

        fake_state = {
            "pid": 42,
            "state": "running",
            "started_at": "2025-01-01T00:00:00",
            "cycle": 5,
        }

        with patch("zsiga.daemon._read_daemon_state", return_value=fake_state), \
             patch("zsiga.daemon._scan_proposal_queue", return_value=[]), \
             patch("zsiga.daemon._compute_uptime_seconds", return_value=100.0):
            result = _build_status_json()

        parsed = json.loads(result)
        assert "daemon" in parsed
        assert parsed["daemon"]["state"] == "running"
        assert parsed["daemon"]["uptime_seconds"] == 100.0
        assert parsed["daemon"]["pid"] == 42


# ── _build_metrics_json ─────────────────────────────────────────────────────


class TestBuildMetricsJson:
    """_build_metrics_json() returns JSON with summary or error."""

    def test_returns_valid_json_with_summary_on_success(self):
        """Scenario: _build_metrics_json returns valid JSON with summary on success"""
        from zsiga.daemon import _build_metrics_json

        with patch("zsiga.metrics.dashboard.compute_stats") as mock_stats:
            mock_stats.return_value = {"summary": {"total": 10}, "phases": {}}
            result = _build_metrics_json()

        parsed = json.loads(result)
        assert "summary" in parsed
        assert parsed["summary"]["total"] == 10

    def test_returns_error_json_on_exception(self):
        """Scenario: _build_metrics_json returns error JSON on exception"""
        from zsiga.daemon import _build_metrics_json

        with patch("zsiga.metrics.dashboard.compute_stats") as mock_stats:
            mock_stats.side_effect = RuntimeError("db locked")
            result = _build_metrics_json()

        parsed = json.loads(result)
        assert "error" in parsed
        assert "db locked" in parsed["error"]
