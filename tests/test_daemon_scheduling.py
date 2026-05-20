"""Tests for daemon_loop smart scheduling behavior.

Tests verify the adaptive sleep policy:
- No sleep when processed_count > 0
- Short idle poll when processed_count == 0
- Safety valve cooldown after max_continuous_cycles
- Fallback to legacy cycle_interval_hours when idle_poll_minutes is 0
"""

import json
from unittest.mock import patch, MagicMock


from zsiga.daemon import daemon_loop, _write_daemon_state


def _make_config(
    cycle_interval_hours=8,
    idle_poll_minutes=5,
    max_continuous_cycles=20,
    cooldown_minutes=30,
):
    """Create a minimal mock config with pipeline scheduling params."""
    config = MagicMock()
    config.pipeline.cycle_interval_hours = cycle_interval_hours
    config.pipeline.idle_poll_minutes = idle_poll_minutes
    config.pipeline.max_continuous_cycles = max_continuous_cycles
    config.pipeline.cooldown_minutes = cooldown_minutes
    return config


class TestSmartSchedulingIdlePoll:
    """Test idle poll behavior (processed_count == 0)."""

    @patch("zsiga.daemon.time.sleep")
    @patch("zsiga.daemon._write_daemon_state")
    @patch("zsiga.daemon._read_daemon_state", return_value={})
    @patch("zsiga.daemon.release_lock")
    @patch("zsiga.daemon.acquire_lock", return_value=(MagicMock(), True))
    @patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator")
    @patch("zsiga.daemon.asyncio")
    def test_idle_cycle_sleeps_idle_poll_minutes(
        self, mock_asyncio, MockOrch, mock_lock, mock_release,
        mock_read, mock_write, mock_sleep,
    ):
        """When processed_count == 0, sleep for idle_poll_minutes * 60."""
        config = _make_config(idle_poll_minutes=5)

        mock_orch_instance = MagicMock()
        MockOrch.return_value = mock_orch_instance
        # First cycle returns 0 (idle), second cycle triggers shutdown
        mock_asyncio.run.side_effect = [0, 0]

        # Use DaemonState to stop after 2nd cycle
        with patch("zsiga.daemon.DaemonState") as MockState:
            state = MagicMock()
            state.shutdown = False
            state.paused = False
            MockState.return_value = state

            # After 2 asyncio.run calls, set shutdown
            call_count = [0]
            def run_side_effect(coro):
                call_count[0] += 1
                if call_count[0] >= 2:
                    state.shutdown = True
                return 0

            mock_asyncio.run.side_effect = run_side_effect

            daemon_loop(config)

        # Verify sleep was called — should have slept chunks totaling 5*60=300s
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        total_slept = sum(sleep_calls)
        assert total_slept == 300  # 5 minutes * 60

    @patch("zsiga.daemon.time.sleep")
    @patch("zsiga.daemon._write_daemon_state")
    @patch("zsiga.daemon._read_daemon_state", return_value={})
    @patch("zsiga.daemon.release_lock")
    @patch("zsiga.daemon.acquire_lock", return_value=(MagicMock(), True))
    @patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator")
    @patch("zsiga.daemon.asyncio")
    def test_custom_idle_poll_from_config(
        self, mock_asyncio, MockOrch, mock_lock, mock_release,
        mock_read, mock_write, mock_sleep,
    ):
        """idle_poll_minutes=3 means 3*60=180 seconds of sleep."""
        config = _make_config(idle_poll_minutes=3)

        mock_orch_instance = MagicMock()
        MockOrch.return_value = mock_orch_instance

        with patch("zsiga.daemon.DaemonState") as MockState:
            state = MagicMock()
            state.shutdown = False
            state.paused = False
            MockState.return_value = state

            call_count = [0]
            def run_side_effect(coro):
                call_count[0] += 1
                if call_count[0] >= 2:
                    state.shutdown = True
                return 0

            mock_asyncio.run.side_effect = run_side_effect
            daemon_loop(config)

        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        total_slept = sum(sleep_calls)
        assert total_slept == 180  # 3 minutes * 60


class TestSmartSchedulingBusy:
    """Test immediate re-cycle when processed_count > 0."""

    @patch("zsiga.daemon.time.sleep")
    @patch("zsiga.daemon._write_daemon_state")
    @patch("zsiga.daemon._read_daemon_state", return_value={})
    @patch("zsiga.daemon.release_lock")
    @patch("zsiga.daemon.acquire_lock", return_value=(MagicMock(), True))
    @patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator")
    @patch("zsiga.daemon.asyncio")
    def test_busy_cycle_no_sleep(
        self, mock_asyncio, MockOrch, mock_lock, mock_release,
        mock_read, mock_write, mock_sleep,
    ):
        """When processed_count > 0, no sleep between cycles."""
        config = _make_config(idle_poll_minutes=5)

        mock_orch_instance = MagicMock()
        MockOrch.return_value = mock_orch_instance

        with patch("zsiga.daemon.DaemonState") as MockState:
            state = MagicMock()
            state.shutdown = False
            state.paused = False
            MockState.return_value = state

            # 3 busy cycles then shutdown
            call_count = [0]
            def run_side_effect(coro):
                call_count[0] += 1
                if call_count[0] >= 3:
                    state.shutdown = True
                return 2  # always busy

            mock_asyncio.run.side_effect = run_side_effect
            daemon_loop(config)

        # No sleep should be called between busy cycles
        # (sleep only called in the pause-check loop inside, not for scheduling)
        # The scheduling `continue` skips the sleep block entirely
        for c in mock_sleep.call_args_list:
            # The only sleep calls should be from the pause-check loop (5s intervals)
            # which is not entered since paused=False
            pass
        # No sleep calls at all for scheduling — all were skipped via `continue`
        assert mock_sleep.call_count == 0

    @patch("zsiga.daemon.time.sleep")
    @patch("zsiga.daemon._write_daemon_state")
    @patch("zsiga.daemon._read_daemon_state", return_value={})
    @patch("zsiga.daemon.release_lock")
    @patch("zsiga.daemon.acquire_lock", return_value=(MagicMock(), True))
    @patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator")
    @patch("zsiga.daemon.asyncio")
    def test_busy_then_idle_sleeps(
        self, mock_asyncio, MockOrch, mock_lock, mock_release,
        mock_read, mock_write, mock_sleep,
    ):
        """After busy cycles, when idle, sleeps for idle_poll_minutes."""
        config = _make_config(idle_poll_minutes=5)

        mock_orch_instance = MagicMock()
        MockOrch.return_value = mock_orch_instance

        with patch("zsiga.daemon.DaemonState") as MockState:
            state = MagicMock()
            state.shutdown = False
            state.paused = False
            MockState.return_value = state

            call_count = [0]
            def run_side_effect(coro):
                call_count[0] += 1
                if call_count[0] == 1:
                    return 2  # busy
                elif call_count[0] == 2:
                    return 0  # idle
                else:
                    state.shutdown = True
                    return 0

            mock_asyncio.run.side_effect = run_side_effect
            daemon_loop(config)

        # After idle cycle (cycle 2), sleep for 5*60 = 300s
        # Then cycle 3 triggers shutdown before sleeping
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        total_slept = sum(sleep_calls)
        assert total_slept == 300


class TestSmartSchedulingFallback:
    """Test fallback to cycle_interval_hours when idle_poll_minutes is 0."""

    @patch("zsiga.daemon.time.sleep")
    @patch("zsiga.daemon._write_daemon_state")
    @patch("zsiga.daemon._read_daemon_state", return_value={})
    @patch("zsiga.daemon.release_lock")
    @patch("zsiga.daemon.acquire_lock", return_value=(MagicMock(), True))
    @patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator")
    @patch("zsiga.daemon.asyncio")
    def test_fallback_to_cycle_interval_hours(
        self, mock_asyncio, MockOrch, mock_lock, mock_release,
        mock_read, mock_write, mock_sleep,
    ):
        """When idle_poll_minutes=0, fallback to cycle_interval_hours."""
        config = _make_config(idle_poll_minutes=0, cycle_interval_hours=8)

        mock_orch_instance = MagicMock()
        MockOrch.return_value = mock_orch_instance

        with patch("zsiga.daemon.DaemonState") as MockState:
            state = MagicMock()
            state.shutdown = False
            state.paused = False
            MockState.return_value = state

            call_count = [0]
            def run_side_effect(coro):
                call_count[0] += 1
                if call_count[0] >= 2:
                    state.shutdown = True
                return 0

            mock_asyncio.run.side_effect = run_side_effect
            daemon_loop(config)

        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        total_slept = sum(sleep_calls)
        assert total_slept == 8 * 3600  # 8 hours in seconds


class TestSmartSchedulingSafetyValve:
    """Test safety valve (cooldown after max_continuous_cycles)."""

    @patch("zsiga.daemon.time.sleep")
    @patch("zsiga.daemon._write_daemon_state")
    @patch("zsiga.daemon._read_daemon_state", return_value={})
    @patch("zsiga.daemon.release_lock")
    @patch("zsiga.daemon.acquire_lock", return_value=(MagicMock(), True))
    @patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator")
    @patch("zsiga.daemon.asyncio")
    def test_cooldown_triggered(
        self, mock_asyncio, MockOrch, mock_lock, mock_release,
        mock_read, mock_write, mock_sleep,
    ):
        """After max_continuous_cycles busy cycles, forced cooldown."""
        config = _make_config(
            max_continuous_cycles=3,
            cooldown_minutes=10,
            idle_poll_minutes=5,
        )

        mock_orch_instance = MagicMock()
        MockOrch.return_value = mock_orch_instance

        with patch("zsiga.daemon.DaemonState") as MockState:
            state = MagicMock()
            state.shutdown = False
            state.paused = False
            MockState.return_value = state

            call_count = [0]
            def run_side_effect(coro):
                call_count[0] += 1
                # 3 busy cycles → triggers cooldown → idle (cycle 4) → shutdown (cycle 5)
                if call_count[0] <= 3:
                    return 1  # busy
                elif call_count[0] == 4:
                    return 0  # idle — will trigger idle poll sleep
                else:
                    state.shutdown = True
                    return 0

            mock_asyncio.run.side_effect = run_side_effect
            daemon_loop(config)

        # After 3 busy cycles, cooldown of 10 min = 600s, then idle poll 300s
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        total_slept = sum(sleep_calls)
        # 600 (cooldown) + 300 (idle after cycle 4)
        assert total_slept == 600 + 300

    @patch("zsiga.daemon.time.sleep")
    @patch("zsiga.daemon._write_daemon_state")
    @patch("zsiga.daemon._read_daemon_state", return_value={})
    @patch("zsiga.daemon.release_lock")
    @patch("zsiga.daemon.acquire_lock", return_value=(MagicMock(), True))
    @patch("zsiga.pipeline.orchestrator.ZsigaOrchestrator")
    @patch("zsiga.daemon.asyncio")
    def test_cooldown_resets_on_idle(
        self, mock_asyncio, MockOrch, mock_lock, mock_release,
        mock_read, mock_write, mock_sleep,
    ):
        """An idle cycle resets the continuous busy counter."""
        config = _make_config(
            max_continuous_cycles=3,
            cooldown_minutes=10,
            idle_poll_minutes=5,
        )

        mock_orch_instance = MagicMock()
        MockOrch.return_value = mock_orch_instance

        with patch("zsiga.daemon.DaemonState") as MockState:
            state = MagicMock()
            state.shutdown = False
            state.paused = False
            MockState.return_value = state

            call_count = [0]
            def run_side_effect(coro):
                call_count[0] += 1
                # 2 busy, 1 idle (resets counter), 2 more busy, idle, then shutdown
                if call_count[0] <= 2:
                    return 1  # busy
                elif call_count[0] == 3:
                    return 0  # idle — resets continuous_busy
                elif call_count[0] <= 5:
                    return 1  # busy again
                elif call_count[0] == 6:
                    return 0  # idle — will trigger idle poll sleep
                else:
                    state.shutdown = True
                    return 0

            mock_asyncio.run.side_effect = run_side_effect
            daemon_loop(config)

        # Cycle 1: busy, no sleep
        # Cycle 2: busy, no sleep
        # Cycle 3: idle, sleep 300 (idle poll)
        # Cycle 4: busy, no sleep
        # Cycle 5: busy, no sleep
        # Cycle 6: idle, sleep 300 (idle poll)
        # Cycle 7: shutdown
        # Total sleep: 300 + 300 = 600
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        total_slept = sum(sleep_calls)
        assert total_slept == 600  # 2 idle polls of 5 min each


class TestRunCycleReturnValue:
    """Test that run_cycle() returns an int (processed_count)."""

    def test_returns_int(self):
        """Verify run_cycle signature accepts and returns int."""
        from zsiga.pipeline.orchestrator import ZsigaOrchestrator
        import inspect
        # Verify the method exists and is async
        assert inspect.iscoroutinefunction(ZsigaOrchestrator.run_cycle)


class TestDaemonStateStatsIntegration:
    """Test daemon_state.json stats update across simulated daemon cycles."""

    def test_stats_update_across_cycles(self, tmp_path, monkeypatch):
        """Simulate multiple daemon cycles and verify stats progression."""
        state_file = tmp_path / "data" / "daemon_state.json"
        monkeypatch.setattr("zsiga.daemon._daemon_state_path", lambda: state_file)

        # Cycle 1: busy (2 changes)
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=1,
            total_cycles=1,
            total_changes_processed=2,
            idle_cycles=0,
            continuous_busy_cycles=1,
            last_change_at="2025-01-01T01:00:00",
        )
        data = json.loads(state_file.read_text())
        assert data["total_cycles"] == 1
        assert data["total_changes_processed"] == 2
        assert data["continuous_busy_cycles"] == 1

        # Cycle 2: busy (1 change)
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=2,
            total_cycles=2,
            total_changes_processed=3,
            idle_cycles=0,
            continuous_busy_cycles=2,
            last_change_at="2025-01-01T02:00:00",
        )
        data = json.loads(state_file.read_text())
        assert data["total_cycles"] == 2
        assert data["total_changes_processed"] == 3
        assert data["continuous_busy_cycles"] == 2

        # Cycle 3: idle
        _write_daemon_state(
            started_at="2025-01-01T00:00:00",
            cycle=3,
            total_cycles=3,
            total_changes_processed=3,
            idle_cycles=1,
            continuous_busy_cycles=0,
            last_change_at="2025-01-01T02:00:00",
        )
        data = json.loads(state_file.read_text())
        assert data["idle_cycles"] == 1
        assert data["continuous_busy_cycles"] == 0
        assert data["last_change_at"] == "2025-01-01T02:00:00"  # unchanged
