"""Tests for daemon cycle error resilience (REQ-DR-01 / REQ-DR-02 / REQ-DR-03)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# REQ-DR-01: Per-proposal error isolation in run_cycle
# ---------------------------------------------------------------------------

class TestPerProposalIsolation:
    """Scenario: Single proposal failure does not abort cycle."""

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.targets = {"proj": MagicMock()}
        config.pipeline.max_changes_per_cycle = 10
        return config

    @pytest.fixture
    def proposals(self):
        return [
            {"id": "prop-1", "project": "proj", "change_dir": "/c1",
             "target_path": "/t", "proposal_filename": "proposal.md",
             "has_specs": True, "has_design": True, "has_tasks": True},
            {"id": "prop-2", "project": "proj", "change_dir": "/c2",
             "target_path": "/t", "proposal_filename": "proposal.md",
             "has_specs": True, "has_design": True, "has_tasks": True},
            {"id": "prop-3", "project": "proj", "change_dir": "/c3",
             "target_path": "/t", "proposal_filename": "proposal.md",
             "has_specs": True, "has_design": True, "has_tasks": True},
        ]

    def test_second_proposal_fails_cycle_continues(self, mock_config, proposals):
        """Processing 2nd proposal raises, but 1st and 3rd still process."""
        with patch("zsiga.pipeline.orchestrator.AgentLoop"), \
             patch("zsiga.pipeline.orchestrator.load_active_context", return_value=None), \
             patch("zsiga.pipeline.orchestrator.DirectoryScanner") as scanner_cls, \
             patch("zsiga.pipeline.orchestrator.read_file", return_value="proposal text"), \
             patch("zsiga.pipeline.orchestrator.decompose") as mock_decompose, \
             patch("zsiga.pipeline.orchestrator.record_lesson"):

            # decompose returns 1 subtask (single-project path)
            mock_decomp = MagicMock()
            mock_decomp.subtasks = [MagicMock()]
            mock_decompose.return_value = mock_decomp

            scanner_cls.return_value.scan.return_value = proposals

            from zsiga.pipeline.orchestrator import ZsigaOrchestrator

            with patch.object(ZsigaOrchestrator, "_process_change", new_callable=AsyncMock) as mock_process:
                # prop-1 succeeds, prop-2 raises, prop-3 succeeds
                mock_process.side_effect = [True, RuntimeError("boom"), True]

                with patch.object(ZsigaOrchestrator, "_update_memory"):
                    orch = ZsigaOrchestrator(mock_config)
                    result = asyncio.run(orch.run_cycle())

                # 2 proposals processed (1st and 3rd), 2nd failed but didn't abort
                assert result == 2
                assert mock_process.call_count == 3

    def test_all_proposals_fail_returns_zero(self, mock_config, proposals):
        """When all proposals raise, processed=0 is returned."""
        with patch("zsiga.pipeline.orchestrator.AgentLoop"), \
             patch("zsiga.pipeline.orchestrator.load_active_context", return_value=None), \
             patch("zsiga.pipeline.orchestrator.DirectoryScanner") as scanner_cls, \
             patch("zsiga.pipeline.orchestrator.read_file", return_value="proposal text"), \
             patch("zsiga.pipeline.orchestrator.decompose") as mock_decompose, \
             patch("zsiga.pipeline.orchestrator.record_lesson"):

            mock_decomp = MagicMock()
            mock_decomp.subtasks = [MagicMock()]
            mock_decompose.return_value = mock_decomp

            scanner_cls.return_value.scan.return_value = proposals

            from zsiga.pipeline.orchestrator import ZsigaOrchestrator

            with patch.object(ZsigaOrchestrator, "_process_change", new_callable=AsyncMock) as mock_process:
                mock_process.side_effect = [RuntimeError("a"), RuntimeError("b"), RuntimeError("c")]

                with patch.object(ZsigaOrchestrator, "_update_memory"):
                    orch = ZsigaOrchestrator(mock_config)
                    result = asyncio.run(orch.run_cycle())

                assert result == 0
                assert mock_process.call_count == 3


# ---------------------------------------------------------------------------
# Helpers for daemon_loop tests
# ---------------------------------------------------------------------------

class _AutoShutdownState:
    """A DaemonState-like object that auto-shuts down after N cycles."""
    def __init__(self, shutdown_after=1):
        self._cycles = 0
        self._shutdown_after = shutdown_after
        self.paused = False

    @property
    def shutdown(self):
        return self._cycles >= self._shutdown_after

    def tick(self):
        self._cycles += 1


def _make_daemon_config():
    config = MagicMock()
    config.pipeline.cycle_interval_hours = 0
    config.pipeline.idle_poll_minutes = 0
    config.pipeline.max_continuous_cycles = 100
    config.pipeline.cooldown_minutes = 0
    return config


def _run_daemon_with_error(tmp_path, monkeypatch, exc_class, exc_msg):
    """Run daemon_loop with an orchestrator that raises on construction.

    Returns list of recorded lesson kwargs.
    """
    from zsiga.daemon import daemon_loop

    monkeypatch.setattr("zsiga.daemon._lock_path", lambda: tmp_path / "lock.pid")
    monkeypatch.setattr("zsiga.daemon._daemon_state_path",
                        lambda: tmp_path / "data" / "daemon_state.json")

    config = _make_daemon_config()
    auto_state = _AutoShutdownState(shutdown_after=1)
    lessons = []

    def capture_lesson(**kwargs):
        lessons.append(kwargs)

    def boom(*args, **kwargs):
        auto_state.tick()
        raise exc_class(exc_msg)

    with patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator", side_effect=boom), \
         patch("zsiga.memory.learn.record_lesson", side_effect=capture_lesson), \
         patch("time.sleep", side_effect=lambda s: None), \
         patch("zsiga.daemon.DaemonState", return_value=auto_state):
        daemon_loop(config)

    return lessons


# ---------------------------------------------------------------------------
# REQ-DR-02: Orchestrator construction error handling
# ---------------------------------------------------------------------------

class TestOrchestratorConstructionError:
    """Scenario: AgentLoop creation fails inside daemon_loop."""

    def test_construction_failure_records_lesson(self, tmp_path, monkeypatch):
        """ZsigaOrchestrator construction fails — lesson recorded, daemon continues."""
        lessons = _run_daemon_with_error(tmp_path, monkeypatch,
                                         RuntimeError, "API unreachable")

        assert len(lessons) >= 1
        lesson = lessons[0]
        assert lesson["pattern_key"] == "daemon.cycle_error"
        assert "RuntimeError" in lesson["context"]
        assert "RuntimeError" in lesson["takeaway"]


# ---------------------------------------------------------------------------
# REQ-DR-03: Structured error diagnostics
# ---------------------------------------------------------------------------

class TestStructuredDiagnostics:
    """Scenario: Cycle error records full traceback with classification."""

    def test_transient_error_tagged(self, tmp_path, monkeypatch):
        """ConnectionError gets [transient] tag."""
        lessons = _run_daemon_with_error(tmp_path, monkeypatch,
                                         ConnectionError, "refused")

        assert len(lessons) >= 1
        lesson = lessons[0]
        assert "[transient]" in lesson["takeaway"]
        assert "ConnectionError" in lesson["takeaway"]
        assert "tb=" in lesson["context"]

    def test_permanent_error_tagged(self, tmp_path, monkeypatch):
        """ValueError gets [permanent] tag."""
        lessons = _run_daemon_with_error(tmp_path, monkeypatch,
                                         ValueError, "bad config")

        assert len(lessons) >= 1
        lesson = lessons[0]
        assert "[permanent]" in lesson["takeaway"]
        assert "ValueError" in lesson["takeaway"]
        assert "cycle=" in lesson["context"]

    def test_lesson_includes_traceback_excerpt(self, tmp_path, monkeypatch):
        """Lesson context includes traceback excerpt."""
        lessons = _run_daemon_with_error(tmp_path, monkeypatch,
                                         OSError, "network")

        assert len(lessons) >= 1
        lesson = lessons[0]
        # Should contain traceback info and exception type
        assert "type=" in lesson["context"]
        assert "OSError" in lesson["context"]
        assert "[transient]" in lesson["takeaway"]
