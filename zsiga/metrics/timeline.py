"""Session Timeline Renderer.

Provides ``render_timeline(session)`` which turns a session summary dict
(as produced by :pymeth:`zsiga.memory.journal.export_session`) into a
multi-line ASCII/Unicode string visualising each phase's duration as a
proportional bar.
"""

from __future__ import annotations

from datetime import datetime

# ── Constants ──────────────────────────────────────────────

_BAR_WIDTH = 40
_FILLED = "\u2588"  # █
_EMPTY = "\u2591"   # ░

_OUTCOME_ICONS = {
    "success": "\u2713",   # ✓
    "fail": "\u2717",      # ✗
    "timeout": "\u23f1",   # ⏱
    "reverted": "\u21a9",  # ↩
    "skipped": "\u2013",   # –
}

_PHASE_NAME_WIDTH = 12


# ── Helpers ────────────────────────────────────────────────


def _outcome_icon(outcome: str) -> str:
    """Return a visual indicator for *outcome*."""
    return _OUTCOME_ICONS.get(outcome, "\u2013")


def _format_duration(seconds: float) -> str:
    """Format *seconds* into a human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def _render_bar(seconds_used: float, total_seconds: float) -> str:
    """Return a proportional bar string of width :data:`_BAR_WIDTH`."""
    if total_seconds <= 0:
        return _EMPTY * _BAR_WIDTH
    ratio = seconds_used / total_seconds
    filled = round(ratio * _BAR_WIDTH)
    filled = max(0, min(_BAR_WIDTH, filled))
    return _FILLED * filled + _EMPTY * (_BAR_WIDTH - filled)


def _format_timestamp(ts: str) -> str:
    """Parse an ISO timestamp and return ``YYYY-MM-DD HH:MM:SS``."""
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ts


def _render_header(session: dict) -> str:
    """Return the header lines of the timeline."""
    change_name = session.get("change_name", "unknown")
    outcome = session.get("outcome", "unknown").upper()
    return f"\u2550\u2550\u2550 {change_name} \u2550\u2550\u2550 [{outcome}]"


def _render_footer(session: dict) -> str:
    """Return the footer line with total runtime and time range."""
    total = session.get("total_runtime_seconds", 0)
    started = _format_timestamp(session.get("started_at", ""))
    finished = _format_timestamp(session.get("finished_at", ""))
    duration = _format_duration(total)
    return f"Total: {duration} \u2502 {started} \u2192 {finished}"


# ── Public API ─────────────────────────────────────────────

_SEPARATOR = "\u2500" * 46  # ───────────────────────────────────────────────


def render_timeline(session: dict) -> str:
    """Render a session summary dict as a multi-line ASCII timeline.

    Parameters
    ----------
    session:
        A dict with keys ``change_name``, ``outcome``, ``started_at``,
        ``finished_at``, ``total_runtime_seconds``, and ``phases`` (a
        list of dicts each having ``phase``, ``outcome``, and
        ``seconds_used``).

    Returns
    -------
    str
        A multi-line string suitable for terminal output, log files, or
        embedding in ``<pre>`` HTML blocks.  Contains **no** ANSI escape
        sequences.
    """
    lines: list[str] = []

    # Header
    lines.append(_render_header(session))
    lines.append(_SEPARATOR)

    phases = session.get("phases", [])
    total_runtime = session.get("total_runtime_seconds", 0)

    if phases:
        for p in phases:
            name = p.get("phase", "?")
            seconds = p.get("seconds_used", 0)
            outcome = p.get("outcome", "")
            bar = _render_bar(seconds, total_runtime)
            icon = _outcome_icon(outcome)
            line = f"{name:<{_PHASE_NAME_WIDTH}}{bar} {seconds:>7.1f}s  {icon}"
            lines.append(line)
    else:
        lines.append("no phases recorded")

    lines.append(_SEPARATOR)

    # Footer
    lines.append(_render_footer(session))

    return "\n".join(lines)
