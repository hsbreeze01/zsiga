"""CLI metric script for verify pass rate analysis."""

from .collector import load_all_changes


def compute_verify_rate_report(
    changes: list[dict] | None = None,
    rolling_window_size: int = 20,
) -> dict:
    """Return a structured dict containing verify pass rate analysis.

    Keys:
        verify_pass_rate_pct  — overall rate
        by_project            — dict of {project_name: pass_rate_pct}
        failure_breakdown     — dict of {category: count}
        rolling_window        — list of {window_end: date, rate: float}
        top_failure_patterns  — list of {category, count, recent_examples}
    """
    if changes is None:
        changes = load_all_changes()

    if not changes:
        return {
            "verify_pass_rate_pct": 0.0,
            "by_project": {},
            "failure_breakdown": {},
            "rolling_window": [],
            "top_failure_patterns": [],
        }

    # Collect verify phases from all changes
    verify_phases = []
    for c in changes:
        for p in c.get("phases", []):
            if p["phase"] == "verify":
                verify_phases.append((c, p))

    # Overall pass rate
    total_verify = len(verify_phases)
    pass_count = sum(
        1 for _, p in verify_phases if p["outcome"] == "success"
    )
    overall_rate = round(pass_count / total_verify * 100, 1) if total_verify else 0.0

    # Per-project breakdown
    by_project: dict[str, dict[str, int]] = {}
    for c, p in verify_phases:
        proj = c.get("project", "unknown")
        if proj not in by_project:
            by_project[proj] = {"total": 0, "pass": 0}
        by_project[proj]["total"] += 1
        if p["outcome"] == "success":
            by_project[proj]["pass"] += 1

    by_project_rates = {
        proj: round(vals["pass"] / vals["total"] * 100, 1)
        for proj, vals in by_project.items()
        if vals["total"] > 0
    }

    # Failure breakdown by category
    failure_breakdown: dict[str, int] = {}
    for c, p in verify_phases:
        if p["outcome"] != "success":
            cat = p.get("failure_category", "") or "unknown"
            failure_breakdown[cat] = failure_breakdown.get(cat, 0) + 1

    # Rolling window
    rolling_window = _compute_rolling_window(
        verify_phases, rolling_window_size
    )

    # Top failure patterns
    top_failure_patterns = _compute_top_failure_patterns(
        verify_phases, changes
    )

    return {
        "verify_pass_rate_pct": overall_rate,
        "by_project": by_project_rates,
        "failure_breakdown": failure_breakdown,
        "rolling_window": rolling_window,
        "top_failure_patterns": top_failure_patterns,
    }


def _compute_rolling_window(
    verify_phases: list[tuple[dict, dict]],
    window_size: int,
) -> list[dict]:
    """Compute rolling verify pass rate over the last N changes."""
    if not verify_phases:
        return []

    results = []
    for i in range(len(verify_phases)):
        start = max(0, i - window_size + 1)
        subset = verify_phases[start : i + 1]
        pass_count = sum(
            1 for _, p in subset if p["outcome"] == "success"
        )
        rate = round(pass_count / len(subset) * 100, 1)
        c, _ = verify_phases[i]
        results.append({
            "window_end": c.get("finished_at", c.get("started_at", "")),
            "rate": rate,
        })

    return results


def _compute_top_failure_patterns(
    verify_phases: list[tuple[dict, dict]],
    changes: list[dict],
) -> list[dict]:
    """Aggregate failure categories with recent change name examples."""
    cat_changes: dict[str, list[str]] = {}
    for c, p in verify_phases:
        if p["outcome"] != "success":
            cat = p.get("failure_category", "") or "unknown"
            if cat not in cat_changes:
                cat_changes[cat] = []
            cat_changes[cat].append(c.get("change_name", "unknown"))

    patterns = []
    for cat, names in sorted(
        cat_changes.items(), key=lambda x: -len(x[1])
    ):
        patterns.append({
            "category": cat,
            "count": len(names),
            "recent_examples": names[-3:],
        })

    return patterns
