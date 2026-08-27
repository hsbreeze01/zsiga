"""Tests for zsiga.daemon — unit tests for path helpers, state I/O, lock
management, queue scanning, status builders, and utility functions.

Spec: openspec/changes/evo-improvement-20260530-134542/specs/daemon-unit-tests.md
"""

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

from zsiga.daemon import (
    _compute_uptime_seconds,
    _daemon_state_path,
    _health_check,
    _lock_path,
    _read_daemon_state,
    _build_metrics_json,
    _build_pipeline_status,
    _build_proposal_detail,
    _build_proposal_stats_json,
    _build_status_json,
    _scan_proposal_queue,
    acquire_lock,
    release_lock,
)


# ── _lock_path ───────────────────────────────────────────────────────


class TestLockPath:
    """Spec: lock_path_resolves_to_data_dir"""

    def test_lock_path_with_zsiga_home_env(self, tmp_path, monkeypatch):
        """_lock_path returns data/lock.pid under ZSIGA_HOME and creates data dir."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        result = _lock_path()
        assert result == tmp_path / "data" / "lock.pid"
        assert (tmp_path / "data").is_dir()

    def test_lock_path_default_without_env(self, monkeypatch):
        """_lock_path returns data/lock.pid under repo root when ZSIGA_HOME unset."""
        monkeypatch.delenv("ZSIGA_HOME", raising=False)
        result = _lock_path()
        assert result.name == "lock.pid"
        assert result.parent.name == "data"


# ── _daemon_state_path ──────────────────────────────────────────────


class TestDaemonStatePath:
    """Spec: daemon_state_path_resolves_to_json"""

    def test_daemon_state_path_with_zsiga_home_env(self, tmp_path, monkeypatch):
        """_daemon_state_path returns data/daemon_state.json under ZSIGA_HOME."""
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        result = _daemon_state_path()
        assert result == tmp_path / "data" / "daemon_state.json"


# ── _read_daemon_state ──────────────────────────────────────────────


class TestReadDaemonState:
    """Spec: read_daemon_state_returns_existing_state"""

    def test_read_daemon_state_valid_file(self, tmp_path, monkeypatch):
        """Returns parsed dict when daemon_state.json contains valid JSON."""
        state_file = tmp_path / "daemon_state.json"
        state_file.write_text(
            '{"pid": 1234, "state": "running"}', encoding="utf-8"
        )
        monkeypatch.setattr(
            "zsiga.daemon._daemon_state_path", lambda: state_file
        )
        result = _read_daemon_state()
        assert result == {"pid": 1234, "state": "running"}

    def test_read_daemon_state_missing_file(self, tmp_path, monkeypatch):
        """Returns empty dict when daemon_state.json does not exist."""
        state_file = tmp_path / "nonexistent" / "daemon_state.json"
        monkeypatch.setattr(
            "zsiga.daemon._daemon_state_path", lambda: state_file
        )
        result = _read_daemon_state()
        assert result == {}

    def test_read_daemon_state_corrupted_json(self, tmp_path, monkeypatch):
        """Returns empty dict when daemon_state.json contains invalid JSON."""
        state_file = tmp_path / "daemon_state.json"
        state_file.write_text("not valid json {{{", encoding="utf-8")
        monkeypatch.setattr(
            "zsiga.daemon._daemon_state_path", lambda: state_file
        )
        result = _read_daemon_state()
        assert result == {}


# ── _compute_uptime_seconds ─────────────────────────────────────────


class TestComputeUptimeSeconds:
    """Spec: compute_uptime_seconds"""

    def test_compute_uptime_valid_timestamp(self):
        """Returns positive float for a recent ISO timestamp."""
        recent = (datetime.now() - timedelta(seconds=5)).isoformat()
        result = _compute_uptime_seconds(recent)
        assert result is not None
        assert isinstance(result, float)
        assert 3.0 <= result <= 8.0  # ±2s tolerance
        assert result == round(result, 1)

    def test_compute_uptime_none_returns_none(self):
        """Returns None when started_at is None."""
        assert _compute_uptime_seconds(None) is None

    def test_compute_uptime_empty_string_returns_none(self):
        """Returns None when started_at is empty string."""
        assert _compute_uptime_seconds("") is None

    def test_compute_uptime_invalid_string_returns_none(self):
        """Returns None when started_at is unparseable."""
        assert _compute_uptime_seconds("not-a-date") is None


# ── _build_status_json ──────────────────────────────────────────────


class TestBuildStatusJson:
    """Spec: build_status_json_structure"""

    def test_build_status_json_valid_structure(self, monkeypatch):
        """Returns valid JSON with daemon and queue keys."""
        now_iso = datetime.now().isoformat()
        monkeypatch.setattr(
            "zsiga.daemon._read_daemon_state",
            lambda: {
                "pid": 42,
                "state": "running",
                "cycle": 1,
                "started_at": now_iso,
            },
        )
        monkeypatch.setattr(
            "zsiga.daemon._scan_proposal_queue", lambda **kw: []
        )
        result = _build_status_json()
        data = json.loads(result)
        assert "daemon" in data
        assert "queue" in data
        assert isinstance(data["queue"], list)
        assert data["daemon"]["pid"] == 42


# ── _build_metrics_json ─────────────────────────────────────────────


class TestBuildMetricsJson:
    """Spec: build_metrics_json_structure"""

    def test_build_metrics_json_on_exception(self, monkeypatch):
        """Returns JSON with error key when compute_stats raises."""
        monkeypatch.setattr(
            "zsiga.metrics.dashboard.compute_stats",
            lambda: (_ for _ in ()).throw(RuntimeError("db unavailable")),
        )
        result = _build_metrics_json()
        data = json.loads(result)
        assert "error" in data
        assert "db unavailable" in data["error"]


# ── _scan_proposal_queue ────────────────────────────────────────────


def _patch_scan_deps(monkeypatch):
    """Monkeypatch external deps used by _scan_proposal_queue."""
    monkeypatch.setattr(
        "zsiga.config.load_config",
        lambda *a, **kw: type("C", (), {"targets": {}})(),
    )
    monkeypatch.setattr("zsiga.metrics.db.load_all_changes", lambda: [])


class TestScanProposalQueue:
    """Spec: scan_proposal_queue_basic"""

    def test_scan_nonexistent_directory_returns_empty(self, tmp_path):
        """Returns empty list for non-existent changes_dir."""
        fake_dir = tmp_path / "no-such-dir"
        result = _scan_proposal_queue(changes_dir=fake_dir)
        assert result == []

    def test_scan_directory_with_proposal_md(self, tmp_path, monkeypatch):
        """Finds proposal and extracts summary from # heading."""
        _patch_scan_deps(monkeypatch)
        change_dir = tmp_path / "my-change"
        change_dir.mkdir()
        (change_dir / "proposal.md").write_text(
            "# Fix logging bug\n\nSome details here.\n", encoding="utf-8"
        )
        result = _scan_proposal_queue(changes_dir=tmp_path)
        assert len(result) == 1
        assert result[0]["name"] == "my-change"
        assert result[0]["summary"] == "Fix logging bug"

    def test_scan_skips_dirs_without_proposal_md(self, tmp_path, monkeypatch):
        """Directories without proposal.md are excluded from the queue."""
        _patch_scan_deps(monkeypatch)
        empty_dir = tmp_path / "no-proposal"
        empty_dir.mkdir()
        result = _scan_proposal_queue(changes_dir=tmp_path)
        assert result == []

    def test_scan_skips_non_directory_entries(self, tmp_path, monkeypatch):
        """Regular files in changes_dir are skipped."""
        _patch_scan_deps(monkeypatch)
        (tmp_path / "not-a-dir.md").write_text("hello", encoding="utf-8")
        result = _scan_proposal_queue(changes_dir=tmp_path)
        assert result == []

    def test_scan_detects_phase_from_files(self, tmp_path, monkeypatch):
        """Phase is IMPLEMENT when clarify.md and specs/ both exist."""
        _patch_scan_deps(monkeypatch)
        change_dir = tmp_path / "phased-change"
        change_dir.mkdir()
        (change_dir / "proposal.md").write_text(
            "# Phase test\n", encoding="utf-8"
        )
        (change_dir / "clarify.md").write_text("clarified", encoding="utf-8")
        specs_dir = change_dir / "specs"
        specs_dir.mkdir()
        (specs_dir / "some-spec.md").write_text("spec", encoding="utf-8")
        result = _scan_proposal_queue(changes_dir=tmp_path)
        assert len(result) == 1
        assert result[0]["phase"] == "IMPLEMENT"


# ── acquire_lock / release_lock ─────────────────────────────────────


class TestAcquireReleaseLock:
    """Spec: acquire_lock_mutual_exclusion, release_lock_cleans_up"""

    def test_acquire_lock_success(self, tmp_path, monkeypatch):
        """acquire_lock returns (fd, True) when no contention."""
        lock_file = tmp_path / "lock.pid"
        monkeypatch.setattr("zsiga.daemon._lock_path", lambda: lock_file)
        fd, ok = acquire_lock()
        assert ok is True
        assert fd is not None
        release_lock(fd)

    def test_acquire_lock_contention_returns_false(self, tmp_path, monkeypatch):
        """Second acquire_lock on same file from subprocess fails."""
        lock_file = tmp_path / "lock.pid"
        monkeypatch.setattr("zsiga.daemon._lock_path", lambda: lock_file)
        fd1, ok1 = acquire_lock()
        assert ok1 is True

        script = (
            "import fcntl; "
            f"f = open('{lock_file}', 'w'); "
            "fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)"
        )
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert proc.returncode != 0 or proc.stderr

        release_lock(fd1)

    def test_release_lock_removes_file(self, tmp_path, monkeypatch):
        """release_lock removes the lock file from disk."""
        lock_file = tmp_path / "lock.pid"
        monkeypatch.setattr("zsiga.daemon._lock_path", lambda: lock_file)
        fd, ok = acquire_lock()
        assert ok is True
        assert lock_file.exists()
        release_lock(fd)
        assert not lock_file.exists()

    def test_release_lock_idempotent_no_error(self, tmp_path, monkeypatch):
        """release_lock does not raise when lock file already removed."""
        lock_file = tmp_path / "lock.pid"
        monkeypatch.setattr("zsiga.daemon._lock_path", lambda: lock_file)
        fd, ok = acquire_lock()
        assert ok is True
        release_lock(fd)
        # File already gone; calling release_lock with a dummy fd should
        # not raise even though the lock file is already deleted.
        dummy_fd = open(tmp_path / "dummy", "w")
        release_lock(dummy_fd)  # Should not raise


# ── _build_proposal_stats_json ──────────────────────────────────────


def _create_changes_table(db_path: str) -> None:
    """Create the changes table in the given SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_name TEXT NOT NULL,
            outcome TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            phases_json TEXT
        )"""
    )
    conn.commit()
    conn.close()


class TestBuildProposalStatsJson:
    """Spec: build_proposal_stats_json_basic"""

    def test_build_proposal_stats_missing_db(self, tmp_path):
        """Returns error dict when db file does not exist."""
        db_path = str(tmp_path / "nonexistent.db")
        result = _build_proposal_stats_json(db_path)
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_build_proposal_stats_valid_db(self, tmp_path):
        """Returns stats from a valid database with one row."""
        db_path = str(tmp_path / "metrics.db")
        _create_changes_table(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO changes (change_name, outcome, started_at, finished_at) "
            "VALUES ('test-proposal', 'success', '2025-01-01T00:00:00', '2025-01-01T01:00:00')"
        )
        conn.commit()
        conn.close()

        result = _build_proposal_stats_json(db_path)
        assert result["total"] == 1
        assert result["by_outcome"] == {"success": 1}
        assert len(result["recent"]) == 1
        assert result["recent"][0]["change_name"] == "test-proposal"

    def test_build_proposal_stats_empty_db(self, tmp_path):
        """Returns zeroed stats from an empty database."""
        db_path = str(tmp_path / "metrics.db")
        _create_changes_table(db_path)

        result = _build_proposal_stats_json(db_path)
        assert result["total"] == 0
        assert result["by_outcome"] == {}
        assert result["recent"] == []


# ── _build_proposal_detail ──────────────────────────────────────────


class TestBuildProposalDetail:
    """Spec: build_proposal_detail_basic"""

    def test_build_proposal_detail_not_found(self, tmp_path):
        """Returns error when proposal directory does not exist."""
        # _build_proposal_detail iterates over the archive dir, so create it
        (tmp_path / "openspec" / "changes" / "archive").mkdir(parents=True)
        result = _build_proposal_detail(
            ":memory:", str(tmp_path), "nonexistent-proposal"
        )
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_build_proposal_detail_found_with_files(self, tmp_path):
        """Returns files content when proposal directory exists."""
        changes_dir = tmp_path / "openspec" / "changes" / "my-proposal"
        changes_dir.mkdir(parents=True)
        (changes_dir / "proposal.md").write_text(
            "# My Proposal", encoding="utf-8"
        )
        (changes_dir / "clarify.md").write_text(
            "Some clarify text", encoding="utf-8"
        )

        result = _build_proposal_detail(
            ":memory:", str(tmp_path), "my-proposal"
        )
        assert result["proposal_name"] == "my-proposal"
        assert "proposal.md" in result["files"]
        assert "clarify.md" in result["files"]
        assert "# My Proposal" in result["files"]["proposal.md"]


# ── _build_pipeline_status ──────────────────────────────────────────


class TestBuildPipelineStatus:
    """Spec: build_pipeline_status_basic"""

    def test_build_pipeline_status_empty_state(self, tmp_path, monkeypatch):
        """Returns default structure when no daemon state or changes exist."""
        monkeypatch.setattr(
            "zsiga.daemon._read_daemon_state", lambda: {}
        )
        result = _build_pipeline_status(":memory:", str(tmp_path))
        assert result["active_proposal"] is None
        assert result["daemon"]["state"] == "unknown"
        assert result["queue"] == []
        assert "phase_progress" in result


# ── _health_check ───────────────────────────────────────────────────


class TestHealthCheck:
    """Spec: health_check_db_probe"""

    def test_health_check_valid_db(self, tmp_path):
        """Returns healthy with correct record count."""
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE changes (id INTEGER PRIMARY KEY, change_name TEXT)"
        )
        for i in range(3):
            conn.execute(
                "INSERT INTO changes (change_name) VALUES (?)",
                (f"change-{i}",),
            )
        conn.commit()
        conn.close()

        result = _health_check(db_path)
        assert result["status"] == "healthy"
        assert result["db_records"] == 3

    def test_health_check_missing_db(self, tmp_path):
        """Returns unhealthy for non-existent database."""
        db_path = str(tmp_path / "nonexistent.db")
        result = _health_check(db_path)
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0
