"""Tests for evolution signal-driven triggering.

Verifies:
1. _signal_threshold_met: requires min outcomes, non-skip, and success
2. _cooldown_elapsed: respects cooldown_hours gap
3. _daily_limit_reached: caps proposals per day
4. should_evolve: integrates all gates
5. daemon.py: Reflector entry removed
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def tmp_base(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "memory").mkdir()
    (tmp_path / "zsiga").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture
def evo_config():
    from zsiga.intake.evolution import EvolutionConfig
    return EvolutionConfig(
        enabled=True,
        window_start_hour=0,
        window_end_hour=24,
        max_per_day=3,
        cooldown_hours=4,
        rejection_breaker=3,
        min_outcomes=5,
        min_non_skip=2,
        min_success=1,
        max_age_hours=48,
    )


@pytest.fixture
def engine(tmp_base, evo_config):
    from zsiga.intake.evolution import EvolutionEngine
    return EvolutionEngine(str(tmp_base), evo_config)


def _write_state(tmp_base, proposals_generated=0, last_proposal_at="", window_start_at=""):
    state_path = tmp_base / "data" / "evolution_state.json"
    state_path.write_text(json.dumps({
        "proposals_generated": proposals_generated,
        "last_proposal_at": last_proposal_at,
        "window_start_at": window_start_at,
        "total_cycles": 0,
    }))


class TestSignalThreshold:
    def test_insufficient_outcomes(self, engine, tmp_base):
        engine._collect_recent_outcomes = lambda: [
            {"name": f"c{i}", "outcome": "success", "ts": datetime.now().isoformat()}
            for i in range(3)
        ]
        assert not engine._signal_threshold_met()

    def test_all_skipped(self, engine, tmp_base):
        engine._collect_recent_outcomes = lambda: [
            {"name": f"c{i}", "outcome": "skipped", "ts": datetime.now().isoformat()}
            for i in range(6)
        ]
        assert not engine._signal_threshold_met()

    def test_sufficient_signals(self, engine, tmp_base):
        now = datetime.now().isoformat()
        engine._collect_recent_outcomes = lambda: [
            {"name": "c1", "outcome": "success", "ts": now},
            {"name": "c2", "outcome": "success", "ts": now},
            {"name": "c3", "outcome": "reverted", "ts": now},
            {"name": "c4", "outcome": "skipped", "ts": now},
            {"name": "c5", "outcome": "skipped", "ts": now},
            {"name": "c6", "outcome": "success", "ts": now},
        ]
        assert engine._signal_threshold_met()

    def test_stale_outcomes_excluded(self, engine, tmp_base):
        old = (datetime.now() - timedelta(hours=72)).isoformat()
        now = datetime.now().isoformat()
        engine._collect_recent_outcomes = lambda: [
            {"name": f"c{i}", "outcome": "success", "ts": old}
            for i in range(10)
        ]
        assert not engine._signal_threshold_met()


class TestCooldown:
    def test_no_prior_proposal(self, engine, tmp_base):
        _write_state(tmp_base)
        assert engine._cooldown_elapsed()

    def test_recent_proposal_blocks(self, engine, tmp_base):
        _write_state(tmp_base, last_proposal_at=datetime.now().isoformat())
        assert not engine._cooldown_elapsed()

    def test_old_proposal_allows(self, engine, tmp_base):
        _write_state(tmp_base, last_proposal_at=(datetime.now() - timedelta(hours=5)).isoformat())
        assert engine._cooldown_elapsed()

    def test_exactly_at_cooldown(self, engine, tmp_base):
        at_boundary = (datetime.now() - timedelta(hours=4, minutes=1)).isoformat()
        _write_state(tmp_base, last_proposal_at=at_boundary)
        assert engine._cooldown_elapsed()


class TestDailyLimit:
    def test_new_day_resets(self, engine, tmp_base):
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        _write_state(tmp_base, proposals_generated=5, window_start_at=yesterday)
        assert not engine._daily_limit_reached()

    def test_limit_reached(self, engine, tmp_base):
        today = datetime.now().date().isoformat()
        _write_state(tmp_base, proposals_generated=3, window_start_at=today)
        assert engine._daily_limit_reached()

    def test_under_limit(self, engine, tmp_base):
        today = datetime.now().date().isoformat()
        _write_state(tmp_base, proposals_generated=2, window_start_at=today)
        assert not engine._daily_limit_reached()


class TestShouldEvolve:
    def test_all_gates_pass(self, engine, tmp_base):
        _write_state(tmp_base)
        now = datetime.now().isoformat()
        engine._collect_recent_outcomes = lambda: [
            {"name": f"c{i}", "outcome": "success" if i < 3 else "skipped", "ts": now}
            for i in range(6)
        ]
        engine._collect_recent_evo_rejections = lambda: []
        engine.is_in_window = lambda: True
        engine.is_paused = lambda: False
        assert engine.should_evolve()

    def test_signal_threshold_blocks(self, engine, tmp_base):
        _write_state(tmp_base)
        engine._collect_recent_outcomes = lambda: []
        engine._collect_recent_evo_rejections = lambda: []
        engine.is_in_window = lambda: True
        engine.is_paused = lambda: False
        assert not engine.should_evolve()

    def test_cooldown_blocks(self, engine, tmp_base):
        _write_state(tmp_base, last_proposal_at=datetime.now().isoformat())
        now = datetime.now().isoformat()
        engine._collect_recent_outcomes = lambda: [
            {"name": f"c{i}", "outcome": "success", "ts": now} for i in range(6)
        ]
        engine._collect_recent_evo_rejections = lambda: []
        engine.is_in_window = lambda: True
        engine.is_paused = lambda: False
        assert not engine.should_evolve()

    def test_rejection_breaker_blocks(self, engine, tmp_base):
        _write_state(tmp_base)
        now = datetime.now().isoformat()
        engine._collect_recent_outcomes = lambda: [
            {"name": f"c{i}", "outcome": "success", "ts": now} for i in range(6)
        ]
        engine._collect_recent_evo_rejections = lambda: [
            {"dir": f"evo-x{i}", "pattern_key": ""} for i in range(3)
        ]
        engine.is_in_window = lambda: True
        engine.is_paused = lambda: False
        assert not engine.should_evolve()


class TestDaemonNoReflectorEntry:
    def test_reflector_import_absent(self):
        content = Path("zsiga/daemon.py").read_text()
        assert "from .intake.reflector import Reflector" not in content
        assert "reflector.run(" not in content

    def test_evolution_rejection_breaker_var_absent(self):
        content = Path("zsiga/daemon.py").read_text()
        assert "evolution_rejection_breaker = " not in content


class TestReflectorSignalsConsumed:
    def test_collect_reflector_signals_returns_list(self, engine, tmp_base):
        result = engine._collect_reflector_signals()
        assert isinstance(result, list)

    def test_phase1_includes_reflector_signals(self, engine, tmp_base):
        (tmp_base / "zsiga" / "__init__.py").write_text("")
        facts = engine._phase1_intake()
        assert "reflector_signals" in facts
        assert isinstance(facts["reflector_signals"], list)
