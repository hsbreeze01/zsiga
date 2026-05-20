"""Tests for zsiga.daemon — _write_daemon_state helper."""

import json
import os

from zsiga.daemon import _write_daemon_state


class TestWriteDaemonState:
    """Test _write_daemon_state writes correct fields."""

    def test_correct_fields_written(self, tmp_path, monkeypatch):
        """All required fields present in daemon_state.json."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=3,
            state="running",
            current_change="fix-logging-bug",
            current_phase="enrich",
            current_project="/home/zsiga/repo",
        )

        assert state_file.exists()
        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["pid"] == os.getpid()
        assert data["started_at"] == "2025-01-01T00:00:00"
        assert data["cycle"] == 3
        assert data["state"] == "running"
        assert data["current_change"] == "fix-logging-bug"
        assert data["current_phase"] == "enrich"
        assert data["current_project"] == "/home/zsiga/repo"
        assert "last_heartbeat" in data
        # Verify heartbeat is a valid ISO timestamp
        from datetime import datetime
        datetime.fromisoformat(data["last_heartbeat"])

    def test_idle_state_sets_nulls(self, tmp_path, monkeypatch):
        """Idle state writes null for current_change, current_phase, current_project."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=5,
            state="running",
            current_change=None,
            current_phase=None,
            current_project=None,
        )

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["current_change"] is None
        assert data["current_phase"] is None
        assert data["current_project"] is None
        assert data["state"] == "running"

    def test_stopped_state(self, tmp_path, monkeypatch):
        """Daemon shutdown writes state=stopped with null fields."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=10,
            state="stopped",
            current_change=None,
            current_phase=None,
            current_project=None,
        )

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["state"] == "stopped"
        assert data["current_change"] is None
        assert data["current_phase"] is None
        assert data["current_project"] is None

    def test_creates_parent_directory(self, tmp_path, monkeypatch):
        """_write_daemon_state creates data/ directory if missing."""
        state_file = tmp_path / "nested" / "dir" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=1,
        )

        assert state_file.exists()

    def test_heartbeat_updates_on_each_write(self, tmp_path, monkeypatch):
        """Each call to _write_daemon_state updates last_heartbeat."""
        import time
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        _write_daemon_state(started_at="2025-01-01T00:00:00", cycle=1)
        data1 = json.loads(state_file.read_text(encoding="utf-8"))

        time.sleep(0.05)

        _write_daemon_state(started_at="2025-01-01T00:00:00", cycle=2)
        data2 = json.loads(state_file.read_text(encoding="utf-8"))

        assert data2["last_heartbeat"] > data1["last_heartbeat"]
        assert data2["cycle"] == 2


class TestDaemonStateStats:
    """Test scheduling statistics fields in daemon_state.json."""

    def test_new_stats_fields_present(self, tmp_path, monkeypatch):
        """New scheduling stats fields are written to daemon_state.json."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=1,
            total_cycles=10,
            total_changes_processed=7,
            idle_cycles=3,
            continuous_busy_cycles=2,
            last_change_at="2025-01-01T07:30:00",
        )

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["total_cycles"] == 10
        assert data["total_changes_processed"] == 7
        assert data["idle_cycles"] == 3
        assert data["continuous_busy_cycles"] == 2
        assert data["last_change_at"] == "2025-01-01T07:30:00"

    def test_stats_default_to_zero_when_not_provided(self, tmp_path, monkeypatch):
        """When no stats provided, defaults to 0 (or None for last_change_at)."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        _write_daemon_state(started_at="2025-01-01T00:00:00", cycle=1)

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["total_cycles"] == 0
        assert data["total_changes_processed"] == 0
        assert data["idle_cycles"] == 0
        assert data["continuous_busy_cycles"] == 0
        assert data["last_change_at"] is None

    def test_stats_persist_across_writes(self, tmp_path, monkeypatch):
        """Stats from a previous write are preserved when not explicitly passed."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        # First write with stats
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=5,
            total_cycles=5,
            total_changes_processed=3,
            idle_cycles=0,
            continuous_busy_cycles=5,
            last_change_at="2025-01-01T05:00:00",
        )

        # Second write without stats — should preserve from previous
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=6,
        )

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["cycle"] == 6
        assert data["total_cycles"] == 5
        assert data["total_changes_processed"] == 3
        assert data["continuous_busy_cycles"] == 5
        assert data["last_change_at"] == "2025-01-01T05:00:00"

    def test_stats_increment_busy_cycle(self, tmp_path, monkeypatch):
        """Simulate a busy cycle: stats update correctly."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        # Initial state
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=5,
            total_cycles=5,
            total_changes_processed=3,
            idle_cycles=0,
            continuous_busy_cycles=0,
            last_change_at="2025-01-01T05:00:00",
        )

        # After busy cycle processing 2 changes
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=6,
            total_cycles=6,
            total_changes_processed=5,
            idle_cycles=0,
            continuous_busy_cycles=1,
            last_change_at="2025-01-01T06:00:00",
        )

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["total_cycles"] == 6
        assert data["total_changes_processed"] == 5
        assert data["continuous_busy_cycles"] == 1
        assert data["idle_cycles"] == 0

    def test_stats_reset_on_idle_cycle(self, tmp_path, monkeypatch):
        """Simulate an idle cycle: continuous_busy resets, idle increments."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        # Busy state
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=5,
            total_cycles=5,
            total_changes_processed=3,
            idle_cycles=0,
            continuous_busy_cycles=3,
            last_change_at="2025-01-01T05:00:00",
        )

        # After idle cycle
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=6,
            total_cycles=6,
            total_changes_processed=3,
            idle_cycles=1,
            continuous_busy_cycles=0,
            last_change_at="2025-01-01T05:00:00",  # unchanged
        )

        data = json.loads(state_file.read_text(encoding="utf-8"))
        assert data["idle_cycles"] == 1
        assert data["continuous_busy_cycles"] == 0
        assert data["last_change_at"] == "2025-01-01T05:00:00"
