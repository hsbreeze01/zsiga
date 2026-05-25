"""Phase budget analysis and adaptive budget recommendations.

Reads historical PhaseRecord data from the DB, computes utilization stats,
and recommends budget adjustments based on actual usage patterns.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional


PHASE_BUDGET_DEFAULTS: dict[str, dict] = {
    "clarify":   {"timeout": 120,  "max_turns": 10},
    "enrich":    {"timeout": 600,  "max_turns": 25},
    "implement": {"timeout": 1200, "max_turns": 50},
    "review":    {"timeout": 180,  "max_turns": 10},
    "verify":    {"timeout": 300,  "max_turns": 12},
    "optimize":  {"timeout": 180,  "max_turns": 5},
    "reflect":   {"timeout": 120,  "max_turns": 3},
    "deliver":   {"timeout": 120,  "max_turns": 5},
}


def get_phase_budget_from_config(config) -> dict[str, dict]:
    """Extract phase budgets from PipelineConfig."""
    p = config.pipeline if hasattr(config, "pipeline") else config
    return {
        "clarify":   {"timeout": 120,  "max_turns": 10},
        "enrich":    {"timeout": getattr(p, "enrich_timeout", 600),    "max_turns": getattr(p, "enrich_max_turns", 25)},
        "implement": {"timeout": getattr(p, "impl_timeout", 1200),     "max_turns": getattr(p, "impl_max_turns", 50)},
        "review":    {"timeout": getattr(p, "review_timeout", 180),    "max_turns": getattr(p, "review_max_turns", 10)},
        "verify":    {"timeout": getattr(p, "verify_timeout", 300),    "max_turns": getattr(p, "verify_max_turns", 12)},
        "optimize":  {"timeout": 180,  "max_turns": 5},
        "reflect":   {"timeout": 120,  "max_turns": 3},
        "deliver":   {"timeout": 120,  "max_turns": 5},
    }


def _pctile(sorted_data: list[float], pct: float) -> float:
    """Compute percentile from sorted list."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * pct / 100.0
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def compute_budget_analysis(db_path: str, config_budgets: Optional[dict[str, dict]] = None) -> dict:
    """Compute per-phase budget utilization analysis from historical data.

    Parameters
    ----------
    db_path : str
        Path to zsiga.db.
    config_budgets : dict or None
        Phase budgets from config (timeout, max_turns per phase).
        If None, uses PHASE_BUDGET_DEFAULTS.

    Returns
    -------
    dict with keys: phases (per-phase stats), summary, recommendations.
    """
    budgets = config_budgets or PHASE_BUDGET_DEFAULTS

    p = Path(db_path)
    if not p.exists():
        return {"error": f"Database not found: {db_path}"}

    phase_data: dict[str, dict] = {}
    for phase_name in budgets:
        phase_data[phase_name] = {
            "durations": [],
            "llm_calls": [],
            "prompt_tokens": [],
            "completion_tokens": [],
            "outcomes": {},
        }

    conn = None
    total_records = 0
    try:
        conn = sqlite3.connect(str(p))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT outcome, phases_json FROM changes").fetchall()

        for row in rows:
            total_records += 1
            phases = json.loads(row["phases_json"]) if row["phases_json"] else []
            for p_rec in phases:
                name = p_rec.get("phase", "")
                if name not in phase_data:
                    continue
                d = phase_data[name]
                dur = p_rec.get("seconds_used", 0)
                if dur > 0:
                    d["durations"].append(dur)
                llm = p_rec.get("llm_calls", 0)
                if llm > 0:
                    d["llm_calls"].append(llm)
                pt = p_rec.get("prompt_tokens", 0)
                ct = p_rec.get("completion_tokens", 0)
                if pt > 0 or ct > 0:
                    d["prompt_tokens"].append(pt)
                    d["completion_tokens"].append(ct)
                outcome = p_rec.get("outcome", "unknown")
                d["outcomes"][outcome] = d["outcomes"].get(outcome, 0) + 1
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        if conn:
            conn.close()

    phases_result = {}
    recommendations = []

    for phase_name, budget in budgets.items():
        d = phase_data[phase_name]
        durs = sorted(d["durations"])
        b_timeout = budget.get("timeout", 0)
        b_turns = budget.get("max_turns", 0)

        count = len(durs)
        if count == 0:
            phases_result[phase_name] = {
                "budget_timeout": b_timeout,
                "budget_max_turns": b_turns,
                "sample_count": 0,
                "status": "no_data",
            }
            continue

        avg_dur = sum(durs) / count
        max_dur = durs[-1]
        p50_dur = _pctile(durs, 50)
        p90_dur = _pctile(durs, 90)
        p95_dur = _pctile(durs, 95)

        total_pt = sum(d["prompt_tokens"])
        total_ct = sum(d["completion_tokens"])
        token_count = len(d["prompt_tokens"]) or 1

        timeout_util_avg = avg_dur / b_timeout if b_timeout > 0 else 0
        timeout_util_max = max_dur / b_timeout if b_timeout > 0 else 0

        timeout_near_hits = sum(1 for x in durs if x >= b_timeout * 0.8)
        timeout_exceeded = sum(1 for x in durs if x >= b_timeout)
        timeout_hit_rate = timeout_near_hits / count

        llm_calls = d["llm_calls"]
        avg_llm = sum(llm_calls) / len(llm_calls) if llm_calls else 0
        max_llm = max(llm_calls) if llm_calls else 0

        success_count = d["outcomes"].get("success", 0)
        success_rate = success_count / count if count > 0 else 0

        if timeout_util_max > 1.0:
            status = "over budget"
        elif timeout_util_max > 0.8:
            status = "tight"
        elif timeout_util_avg < 0.15 and b_timeout > 300:
            status = "oversized"
        else:
            status = "healthy"

        recommended_timeout = max(int(p95_dur * 1.5), 60)
        recommended_timeout = min(recommended_timeout, 3600)

        phases_result[phase_name] = {
            "budget_timeout": b_timeout,
            "budget_max_turns": b_turns,
            "sample_count": count,
            "status": status,
            "duration": {
                "avg": round(avg_dur, 1),
                "p50": round(p50_dur, 1),
                "p90": round(p90_dur, 1),
                "p95": round(p95_dur, 1),
                "max": round(max_dur, 1),
            },
            "utilization": {
                "timeout_avg_pct": round(timeout_util_avg * 100, 1),
                "timeout_max_pct": round(timeout_util_max * 100, 1),
                "timeout_near_hits": timeout_near_hits,
                "timeout_exceeded": timeout_exceeded,
                "timeout_hit_rate": round(timeout_hit_rate * 100, 1),
            },
            "tokens": {
                "avg_prompt": round(total_pt / token_count),
                "avg_completion": round(total_ct / token_count),
                "avg_total": round((total_pt + total_ct) / token_count),
            },
            "llm_calls": {
                "avg": round(avg_llm, 1),
                "max": max_llm,
            },
            "outcomes": d["outcomes"],
            "recommended_timeout": recommended_timeout,
        }

        if status == "over budget":
            recommendations.append({
                "phase": phase_name,
                "severity": "high",
                "issue": f"Phase exceeded timeout budget (max {max_dur:.0f}s vs budget {b_timeout}s)",
                "suggestion": f"Increase timeout to >= {recommended_timeout}s (p95={p95_dur:.0f}s * 1.5)",
                "current": b_timeout,
                "recommended": recommended_timeout,
            })
        elif status == "tight":
            recommendations.append({
                "phase": phase_name,
                "severity": "medium",
                "issue": f"Phase approaching timeout limit (max {max_dur:.0f}s = {timeout_util_max*100:.0f}% of budget)",
                "suggestion": f"Consider increasing timeout to {recommended_timeout}s",
                "current": b_timeout,
                "recommended": recommended_timeout,
            })
        elif status == "oversized":
            recommended_down = max(int(p95_dur * 2), 120)
            if recommended_down < b_timeout * 0.5:
                recommendations.append({
                    "phase": phase_name,
                    "severity": "low",
                    "issue": f"Phase budget oversized (avg {avg_dur:.0f}s, budget {b_timeout}s, {timeout_util_avg*100:.0f}% utilization)",
                    "suggestion": f"Consider reducing timeout to {recommended_down}s to reclaim budget for other phases",
                    "current": b_timeout,
                    "recommended": recommended_down,
                })

    total_timeout_budget = sum(b.get("timeout", 0) for b in budgets.values())
    healthy_count = sum(1 for v in phases_result.values() if v.get("status") == "healthy")
    total_phases = len(budgets)

    return {
        "total_records": total_records,
        "phases": phases_result,
        "summary": {
            "total_timeout_budget": total_timeout_budget,
            "healthy_phases": healthy_count,
            "total_phases": total_phases,
            "health_pct": round(healthy_count / total_phases * 100, 1) if total_phases > 0 else 0,
        },
        "recommendations": recommendations,
    }


def recommend_phase_budget(phase_name: str, db_path: str,
                           config_budgets: Optional[dict[str, dict]] = None) -> dict:
    """Get budget recommendation for a single phase.

    Returns a dict with: current_timeout, recommended_timeout, max_observed, p95.
    """
    budgets = config_budgets or PHASE_BUDGET_DEFAULTS
    budget = budgets.get(phase_name, {})
    b_timeout = budget.get("timeout", 120)

    p = Path(db_path)
    if not p.exists():
        return {"current_timeout": b_timeout, "recommended_timeout": b_timeout, "error": "no db"}

    durs = []
    conn = None
    try:
        conn = sqlite3.connect(str(p))
        rows = conn.execute("SELECT phases_json FROM changes").fetchall()
        for row in rows:
            phases = json.loads(row[0]) if row[0] else []
            for p_rec in phases:
                if p_rec.get("phase") == phase_name:
                    dur = p_rec.get("seconds_used", 0)
                    if dur > 0:
                        durs.append(dur)
    except Exception:
        return {"current_timeout": b_timeout, "recommended_timeout": b_timeout}
    finally:
        if conn:
            conn.close()

    if not durs:
        return {"current_timeout": b_timeout, "recommended_timeout": b_timeout, "sample_count": 0}

    durs.sort()
    p95 = _pctile(durs, 95)
    max_dur = durs[-1]
    recommended = max(int(p95 * 1.5), 60)

    return {
        "current_timeout": b_timeout,
        "recommended_timeout": recommended,
        "max_observed": round(max_dur, 1),
        "p95": round(p95, 1),
        "sample_count": len(durs),
    }
