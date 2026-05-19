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
