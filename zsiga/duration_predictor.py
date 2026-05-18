"""Duration predictor for pipeline phases.

Estimates per-phase durations using linear regression on historical data,
with a median-based fallback when data is insufficient.
"""

from __future__ import annotations

from statistics import median

DEFAULT_PHASE_SECONDS = 30.0


def _collect_known_phases(phase_stats: list[dict]) -> set[str]:
    """Extract all unique phase names from historical records."""
    phases: set[str] = set()
    for record in phase_stats:
        phases.update(record.get("phases", {}).keys())
    return phases


def _fit_linear(xs1: list[float], xs2: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Least-squares fit for y = a*x1 + b*x2 + c.

    Solves the normal equations for the 2-feature linear model using
    pure Python arithmetic (no numpy needed).
    Returns coefficients (a, b, c).
    """
    n = len(ys)
    if n == 0:
        return (0.0, 0.0, 0.0)

    # Compute sums
    s_x1 = sum(xs1)
    s_x2 = sum(xs2)
    s_y = sum(ys)
    s_x1x1 = sum(x * x for x in xs1)
    s_x2x2 = sum(x * x for x in xs2)
    s_x1x2 = sum(a * b for a, b in zip(xs1, xs2))
    s_x1y = sum(a * b for a, b in zip(xs1, ys))
    s_x2y = sum(a * b for a, b in zip(xs2, ys))

    # Normal equation: A^T A * [a, b, c]^T = A^T y
    # Matrix M = [[s_x1x1, s_x1x2, s_x1],
    #             [s_x1x2, s_x2x2, s_x2],
    #             [s_x1,   s_x2,   n  ]]
    # Vector v = [s_x1y, s_x2y, s_y]
    # Solve via Cramer's rule (3x3 determinant)

    def det3(m: list[list[float]]) -> float:
        return (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )

    M = [
        [s_x1x1, s_x1x2, s_x1],
        [s_x1x2, s_x2x2, s_x2],
        [s_x1, s_x2, float(n)],
    ]
    v = [s_x1y, s_x2y, s_y]

    D = det3(M)
    if abs(D) < 1e-12:
        # Degenerate / collinear — fall back to mean
        mean_y = s_y / n if n > 0 else 0.0
        return (0.0, 0.0, mean_y)

    # Cramer's rule: replace column i with v
    a = det3([v, M[1], M[2]]) / D  # noqa: E741
    b = det3([M[0], v, M[2]]) / D
    c = det3([M[0], M[1], v]) / D

    return (a, b, c)


def _predict_phase(
    records: list[dict],
    phase_name: str,
    project_lines: int,
    proposal_chars: int,
) -> float:
    """Predict duration for a single phase using linear regression.

    Returns a clamped (>= 0.0) predicted duration in seconds.
    """
    xs1: list[float] = []
    xs2: list[float] = []
    ys: list[float] = []

    for rec in records:
        phase_duration = rec.get("phases", {}).get(phase_name)
        if phase_duration is None:
            continue
        xs1.append(float(rec["project_lines"]))
        xs2.append(float(rec["proposal_chars"]))
        ys.append(float(phase_duration))

    if len(ys) < 3:
        # Not enough data for regression; use median fallback
        if ys:
            return median(ys)
        return DEFAULT_PHASE_SECONDS

    a, b, c = _fit_linear(xs1, xs2, ys)
    predicted = a * project_lines + b * proposal_chars + c
    return max(0.0, predicted)


def _fallback_estimates(phase_stats: list[dict]) -> dict[str, float]:
    """Compute median-based fallback estimates when data is insufficient.

    Returns a dict mapping each known phase to its median duration,
    or DEFAULT_PHASE_SECONDS if no data exists for that phase.
    Also includes a ``_total`` key.
    """
    known_phases = _collect_known_phases(phase_stats)
    result: dict[str, float] = {}

    for phase in sorted(known_phases):
        durations = [
            rec["phases"][phase]
            for rec in phase_stats
            if phase in rec.get("phases", {})
        ]
        if durations:
            result[phase] = median(durations)
        else:
            result[phase] = DEFAULT_PHASE_SECONDS

    result["_total"] = sum(v for k, v in result.items() if k != "_total")
    return result


def predict_change_duration(
    phase_stats: list[dict],
    project_lines: int,
    proposal_chars: int,
) -> dict[str, float]:
    """Estimate per-phase durations for a proposed change.

    Args:
        phase_stats: List of historical records, each with ``project_lines``,
            ``proposal_chars``, and ``phases`` (dict of phase_name → seconds).
        project_lines: LOC of the target project.
        proposal_chars: Character count of the proposal text.

    Returns:
        Dict mapping each known phase name to estimated seconds (float),
        plus a ``_total`` key that is the sum of all per-phase estimates.
    """
    if len(phase_stats) < 3:
        return _fallback_estimates(phase_stats)

    known_phases = _collect_known_phases(phase_stats)
    result: dict[str, float] = {}

    for phase in known_phases:
        result[phase] = _predict_phase(phase_stats, phase, project_lines, proposal_chars)

    result["_total"] = sum(v for k, v in result.items() if k != "_total")
    return result
