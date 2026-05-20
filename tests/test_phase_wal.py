"""Tests for the Phase WAL module (pipeline/phase_wal.py)."""

import tempfile

from zsiga.pipeline.phase_wal import PhaseWAL
from zsiga.transport import LocalTransport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_wal(tmpdir: str | None = None) -> tuple[PhaseWAL, str]:
    """Create a PhaseWAL backed by a real temp directory."""
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp(prefix="phase_wal_test_")
    transport = LocalTransport()
    wal = PhaseWAL(change_dir=tmpdir, transport=transport)
    return wal, tmpdir


# ---------------------------------------------------------------------------
# REQ-WAL-02: Write and read round-trip
# ---------------------------------------------------------------------------


class TestWriteReadRoundTrip:
    """Scenario: Write and read round-trip."""

    def test_write_then_read_returns_all_keys(self):
        """Given a PhaseWAL, when write() is called, read() returns all keys."""
        wal, tmpdir = _make_wal()
        wal.write(
            phase="implement",
            pre_sha="abc123",
            target_path="/repo",
            project="my-project",
        )

        assert wal.exists() is True
        data = wal.read()
        assert data is not None
        assert data["current_phase"] == "implement"
        assert data["pre_sha"] == "abc123"
        assert data["target_path"] == "/repo"
        assert data["project"] == "my-project"
        assert "started_at" in data

    def test_started_at_is_iso_format(self):
        """started_at shall be a valid ISO-8601 timestamp."""
        wal, _ = _make_wal()
        wal.write(phase="enrich")

        data = wal.read()
        assert data is not None
        from datetime import datetime
        datetime.fromisoformat(data["started_at"])  # should not raise

    def test_optional_fields_omitted_when_not_provided(self):
        """When optional fields are not passed, they are absent from the file."""
        wal, _ = _make_wal()
        wal.write(phase="enrich")

        data = wal.read()
        assert data is not None
        assert data["current_phase"] == "enrich"
        assert "pre_sha" not in data
        assert "target_path" not in data
        assert "project" not in data


# ---------------------------------------------------------------------------
# REQ-WAL-02: Delete WAL
# ---------------------------------------------------------------------------


class TestDeleteWAL:
    """Scenario: Delete WAL."""

    def test_delete_removes_file(self):
        """Given an existing .phase_state, delete() removes it."""
        wal, _ = _make_wal()
        wal.write(phase="implement", pre_sha="abc123")
        assert wal.exists() is True

        wal.delete()

        assert wal.exists() is False
        assert wal.read() is None

    def test_delete_is_idempotent(self):
        """Calling delete() on a non-existent WAL does not raise."""
        wal, _ = _make_wal()
        wal.delete()  # should not raise
        assert wal.exists() is False


# ---------------------------------------------------------------------------
# REQ-WAL-02: Read non-existent WAL
# ---------------------------------------------------------------------------


class TestReadNonExistent:
    """Scenario: Read non-existent WAL."""

    def test_read_returns_none_when_no_file(self):
        """Given no .phase_state, read() returns None."""
        wal, _ = _make_wal()
        assert wal.read() is None
        assert wal.exists() is False


# ---------------------------------------------------------------------------
# WAL at each phase boundary
# ---------------------------------------------------------------------------


class TestPhaseBoundaries:
    """Verify WAL content for each pipeline phase."""

    def test_enrich_phase(self):
        wal, _ = _make_wal()
        wal.write(phase="enrich")
        assert wal.read()["current_phase"] == "enrich"

    def test_implement_phase(self):
        wal, _ = _make_wal()
        wal.write(phase="implement", pre_sha="deadbeef")
        data = wal.read()
        assert data["current_phase"] == "implement"
        assert data["pre_sha"] == "deadbeef"

    def test_verify_phase(self):
        wal, _ = _make_wal()
        wal.write(phase="verify", pre_sha="deadbeef")
        data = wal.read()
        assert data["current_phase"] == "verify"
        assert data["pre_sha"] == "deadbeef"

    def test_overwrite_updates_phase(self):
        """Writing again overwrites the previous state."""
        wal, _ = _make_wal()
        wal.write(phase="enrich")
        assert wal.read()["current_phase"] == "enrich"

        wal.write(phase="implement", pre_sha="abc")
        data = wal.read()
        assert data["current_phase"] == "implement"
        assert data["pre_sha"] == "abc"
