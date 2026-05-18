"""Tests for zsiga.metrics.timeline."""

from __future__ import annotations

from zsiga.metrics.timeline import (
    _format_duration,
    _format_timestamp,
    _outcome_icon,
    _render_bar,
    render_timeline,
)


# ── Fixtures ───────────────────────────────────────────────

def _make_session(
    *,
    change_name: str = "add-health-endpoint",
    outcome: str = "success",
    started_at: str = "2026-05-15T14:00:00",
    finished_at: str = "2026-05-15T14:05:00",
    total_runtime_seconds: float = 300.0,
    phases: list[dict] | None = None,
) -> dict:
    if phases is None:
        phases = [
            {"phase": "enrich", "outcome": "success", "seconds_used": 45.0},
            {"phase": "implement", "outcome": "success", "seconds_used": 150.0},
            {"phase": "verify", "outcome": "success", "seconds_used": 60.0},
            {"phase": "deliver", "outcome": "success", "seconds_used": 45.0},
        ]
    return {
        "change_name": change_name,
        "outcome": outcome,
        "started_at": started_at,
        "finished_at": finished_at,
        "total_runtime_seconds": total_runtime_seconds,
        "phases": phases,
    }


# ── Unit: helper functions ─────────────────────────────────


class TestOutcomeIcon:
    def test_success(self):
        assert _outcome_icon("success") == "\u2713"

    def test_fail(self):
        assert _outcome_icon("fail") == "\u2717"

    def test_timeout(self):
        assert _outcome_icon("timeout") == "\u23f1"

    def test_reverted(self):
        assert _outcome_icon("reverted") == "\u21a9"

    def test_skipped(self):
        assert _outcome_icon("skipped") == "\u2013"

    def test_unknown(self):
        assert _outcome_icon("banana") == "\u2013"


class TestFormatDuration:
    def test_seconds_only(self):
        assert _format_duration(45.0) == "45.0s"

    def test_minutes_and_seconds(self):
        result = _format_duration(318.0)
        assert result == "5m 18s"

    def test_exact_minutes(self):
        assert _format_duration(120.0) == "2m 0s"

    def test_hours(self):
        assert _format_duration(3700.0) == "1h 1m"


class TestRenderBar:
    def test_proportional_bars(self):
        """25% of 40 = 10 filled chars."""
        bar = _render_bar(50.0, 200.0)
        filled = bar.count("\u2588")
        empty = bar.count("\u2591")
        assert filled == 10
        assert empty == 30
        assert len(bar) == 40

    def test_full_bar(self):
        bar = _render_bar(100.0, 100.0)
        assert bar == "\u2588" * 40

    def test_zero_bar(self):
        bar = _render_bar(0.0, 100.0)
        assert bar == "\u2591" * 40

    def test_zero_total_runtime(self):
        bar = _render_bar(0.0, 0.0)
        assert bar == "\u2591" * 40


class TestFormatTimestamp:
    def test_iso_format(self):
        assert _format_timestamp("2026-05-15T14:00:00") == "2026-05-15 14:00:00"

    def test_empty(self):
        assert _format_timestamp("") == "N/A"

    def test_invalid(self):
        assert _format_timestamp("not-a-date") == "not-a-date"


# ── Integration: render_timeline ───────────────────────────


class TestRenderTimelineMultiPhase:
    """REQ-TL-01 Scenario: Render a session with multiple phases."""

    def test_contains_header(self):
        out = render_timeline(_make_session())
        assert "add-health-endpoint" in out
        assert "[SUCCESS]" in out

    def test_contains_all_phases(self):
        out = render_timeline(_make_session())
        for name in ["enrich", "implement", "verify", "deliver"]:
            assert name in out

    def test_contains_duration_seconds(self):
        out = render_timeline(_make_session())
        assert "45.0s" in out
        assert "150.0s" in out

    def test_contains_outcome_icons(self):
        out = render_timeline(_make_session())
        assert "\u2713" in out

    def test_contains_footer(self):
        out = render_timeline(_make_session())
        assert "2026-05-15" in out
        assert "14:00:00" in out

    def test_proportional_bar_for_implement(self):
        """implement = 150/300 = 50% → 20 filled blocks."""
        out = render_timeline(_make_session())
        for line in out.splitlines():
            if "implement" in line:
                assert line.count("\u2588") == 20
                break
        else:
            raise AssertionError("implement line not found")


class TestRenderTimelineSinglePhase:
    """REQ-TL-01 Scenario: Render a session with a single phase."""

    def test_single_phase_full_bar(self):
        session = _make_session(
            total_runtime_seconds=120.0,
            phases=[{"phase": "implement", "outcome": "success", "seconds_used": 120.0}],
        )
        out = render_timeline(session)
        for line in out.splitlines():
            if "implement" in line:
                assert line.count("\u2588") == 40
                break
        else:
            raise AssertionError("implement line not found")

    def test_footer_shows_total(self):
        session = _make_session(
            total_runtime_seconds=120.0,
            phases=[{"phase": "implement", "outcome": "success", "seconds_used": 120.0}],
        )
        out = render_timeline(session)
        assert "2m 0s" in out


class TestRenderTimelineZeroPhases:
    """REQ-TL-01 Scenario: Render a session with zero phases."""

    def test_no_phases_message(self):
        session = _make_session(phases=[])
        out = render_timeline(session)
        assert "no phases recorded" in out

    def test_header_present(self):
        session = _make_session(phases=[])
        out = render_timeline(session)
        assert "add-health-endpoint" in out

    def test_no_phase_rows(self):
        session = _make_session(phases=[])
        out = render_timeline(session)
        # Should not contain any of the standard phase names as row entries
        for line in out.splitlines():
            # Lines with bars are phase rows
            assert "\u2588" not in line


class TestProportionalBars:
    """REQ-TL-02: Proportional duration bars."""

    def test_varying_durations(self):
        session = _make_session(
            total_runtime_seconds=200.0,
            phases=[
                {"phase": "enrich", "outcome": "success", "seconds_used": 50.0},
                {"phase": "implement", "outcome": "success", "seconds_used": 100.0},
                {"phase": "verify", "outcome": "success", "seconds_used": 30.0},
                {"phase": "deliver", "outcome": "success", "seconds_used": 20.0},
            ],
        )
        out = render_timeline(session)
        for line in out.splitlines():
            if "enrich" in line:
                assert line.count("\u2588") == 10  # 25% of 40
            elif "implement" in line:
                assert line.count("\u2588") == 20  # 50% of 40

    def test_zero_runtime(self):
        session = _make_session(
            total_runtime_seconds=0,
            phases=[
                {"phase": "implement", "outcome": "success", "seconds_used": 0.0},
            ],
        )
        out = render_timeline(session)
        for line in out.splitlines():
            if "implement" in line:
                assert line.count("\u2588") == 0
                break


class TestPhaseOutcomeIndicators:
    """REQ-TL-03: Phase outcome indicators."""

    def test_failed_indicator(self):
        session = _make_session(
            phases=[
                {"phase": "implement", "outcome": "fail", "seconds_used": 150.0},
            ],
        )
        out = render_timeline(session)
        assert "\u2717" in out

    def test_timeout_indicator(self):
        session = _make_session(
            phases=[
                {"phase": "verify", "outcome": "timeout", "seconds_used": 60.0},
            ],
        )
        out = render_timeline(session)
        assert "\u23f1" in out

    def test_reverted_indicator(self):
        session = _make_session(
            phases=[
                {"phase": "deliver", "outcome": "reverted", "seconds_used": 10.0},
            ],
        )
        out = render_timeline(session)
        assert "\u21a9" in out


class TestNoAnsiCodes:
    """REQ-TL-04: No ANSI escape codes in output."""

    def test_no_escape_sequences(self):
        session = _make_session()
        out = render_timeline(session)
        assert b"\x1b" not in out.encode("utf-8")

    def test_no_escape_various_sessions(self):
        for outcome in ["success", "fail", "timeout", "reverted", "skipped"]:
            session = _make_session(
                outcome=outcome,
                phases=[
                    {"phase": "implement", "outcome": outcome, "seconds_used": 50.0},
                ],
            )
            out = render_timeline(session)
            assert b"\x1b" not in out.encode("utf-8")


class TestTimeRangeDisplay:
    """REQ-TL-05: Session time range display."""

    def test_time_range_formatting(self):
        session = _make_session(
            started_at="2026-05-15T14:00:00",
            finished_at="2026-05-15T14:05:18",
            total_runtime_seconds=318.0,
        )
        out = render_timeline(session)
        assert "2026-05-15 14:00:00" in out
        assert "2026-05-15 14:05:18" in out
        assert "5m 18s" in out
