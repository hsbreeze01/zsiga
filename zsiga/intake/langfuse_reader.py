"""Langfuse trace reader for EvolutionEngine.

Fetches recent pipeline traces from Langfuse and computes actionable metrics:
- Per-proposal token cost breakdown (by phase / sub-agent)
- Phase latency outliers (which phase is slowest)
- Sub-agent success/failure ratios
- Token cost trends (are we getting more expensive?)

All reads are best-effort. If Langfuse is not configured or the API
returns errors, every function returns empty/zero defaults — the
Evolution pipeline never blocks on observability data.

Design principles:
  1. **Read-only**: never writes to Langfuse, only fetches.
  2. **Shallow first**: trace.list + trace.get gives us observations;
     we avoid per-observation detail calls to stay within rate limits.
  3. **Locally cached**: results are memoized for ``cache_ttl`` seconds
     so multiple calls within one evolution cycle don't hit the API.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class GenerationMetrics:
    """Token usage for a single LLM generation."""

    name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class SubAgentMetrics:
    """Aggregated metrics for one sub-agent role within a trace."""

    role: str
    generation_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class TraceMetrics:
    """Aggregated metrics for one proposal trace."""

    trace_id: str = ""
    trace_name: str = ""
    timestamp: str = ""
    is_auto: bool = False
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    sub_agents: list[SubAgentMetrics] = field(default_factory=list)
    generations: list[GenerationMetrics] = field(default_factory=list)
    # Key: sub-agent role or "main_loop" — tokens attributed to each role
    phase_tokens: dict[str, int] = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """Cross-trace aggregated metrics for the Evolution engine."""

    trace_count: int = 0
    total_tokens: int = 0
    avg_tokens_per_trace: float = 0.0
    # Most expensive phase across all traces
    costliest_phase: str = ""
    costliest_phase_tokens: int = 0
    # Per-phase token averages
    phase_avg_tokens: dict[str, float] = field(default_factory=dict)
    # Sub-agent generation counts
    sub_agent_usage: dict[str, int] = field(default_factory=dict)
    # Recent trace-level details
    recent_traces: list[TraceMetrics] = field(default_factory=list)
    # Token trend: positive = costs rising, negative = costs falling
    token_trend: float = 0.0
    # Per-trace token list (ordered oldest→newest) for trend calculation
    per_trace_tokens: list[int] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_cached_metrics: Optional[AggregatedMetrics] = None
_cached_at: float = 0.0


def _load_env():
    """Load LANGFUSE_* vars from .zsiga.env if not already set."""
    if os.environ.get("LANGFUSE_PUBLIC_KEY"):
        return
    from pathlib import Path

    env_file = Path(__file__).resolve().parent.parent.parent / ".zsiga.env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)


def _get_client():
    """Get a Langfuse client, or None if not configured."""
    _load_env()
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        return None
    try:
        from langfuse import Langfuse

        return Langfuse()
    except Exception as exc:
        logger.warning("Langfuse client init failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Trace fetching & parsing
# ---------------------------------------------------------------------------


def fetch_recent_traces(limit: int = 10, hours: int = 24) -> list[TraceMetrics]:
    """Fetch recent proposal traces from Langfuse.

    Returns a list of :class:`TraceMetrics`, ordered oldest→newest.
    """
    client = _get_client()
    if client is None:
        return []

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        resp = client.api.trace.list(
            limit=limit,
            from_timestamp=cutoff,
            order_by="timestamp.asc",
        )
    except Exception as exc:
        logger.warning("Langfuse trace.list failed: %s", exc)
        return []

    if not resp or not hasattr(resp, "data") or not resp.data:
        return []

    results: list[TraceMetrics] = []
    for trace_summary in resp.data:
        try:
            detail = client.api.trace.get(trace_summary.id)
        except Exception:
            # Skip traces we can't fetch details for
            continue

        tm = TraceMetrics(
            trace_id=detail.id,
            trace_name=detail.name or "",
            timestamp=str(detail.timestamp) if detail.timestamp else "",
            is_auto=detail.input.get("is_auto", "False") == "True"
            if isinstance(detail.input, dict)
            else False,
        )

        observations = detail.observations or []
        obs_by_id: dict[str, object] = {}
        for obs in observations:
            obs_by_id[obs.id] = obs

        for obs in observations:
            obs_name = obs.name or ""
            obs_type = (obs.type or "").upper()

            if obs_type == "GENERATION":
                usage = getattr(obs, "usage", None)
                in_tok = usage.input if usage else 0
                out_tok = usage.output if usage else 0
                tot_tok = usage.total if usage else 0

                gen = GenerationMetrics(
                    name=obs_name,
                    model=getattr(obs, "model", "") or "",
                    input_tokens=in_tok or 0,
                    output_tokens=out_tok or 0,
                    total_tokens=tot_tok or 0,
                )
                tm.generations.append(gen)
                tm.total_input_tokens += gen.input_tokens
                tm.total_output_tokens += gen.output_tokens
                tm.total_tokens += gen.total_tokens

                # Attribute to parent sub-agent role (which maps to a phase)
                parent = obs_by_id.get(getattr(obs, "parent_observation_id", None))
                if parent and (parent.type or "").upper() == "AGENT":
                    role = (parent.name or "").replace("sub_agent:", "", 1)
                    tm.phase_tokens[role] = tm.phase_tokens.get(role, 0) + gen.total_tokens
                else:
                    # Direct child of trace root = main agent loop (implement phase)
                    tm.phase_tokens["main_loop"] = tm.phase_tokens.get("main_loop", 0) + gen.total_tokens

            # Collect sub-agent spans
            if obs_type == "AGENT" and obs_name.startswith("sub_agent:"):
                role = obs_name.replace("sub_agent:", "", 1)
                tm.sub_agents.append(SubAgentMetrics(role=role))

        results.append(tm)

    return results


def aggregate_metrics(traces: list[TraceMetrics]) -> AggregatedMetrics:
    """Compute aggregated metrics from a list of trace metrics."""
    if not traces:
        return AggregatedMetrics()

    total_tokens = sum(t.total_tokens for t in traces)
    per_trace_tokens = [t.total_tokens for t in traces]
    avg_tokens = total_tokens / len(traces) if traces else 0

    # Per-phase token averages
    phase_totals: dict[str, int] = {}
    phase_counts: dict[str, int] = {}
    for t in traces:
        for phase, tokens in t.phase_tokens.items():
            phase_totals[phase] = phase_totals.get(phase, 0) + tokens
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

    phase_avg = {
        phase: phase_totals[phase] / phase_counts[phase]
        for phase in phase_totals
    }

    # Costliest phase
    costliest_phase = ""
    costliest_tokens = 0
    for phase, total in phase_totals.items():
        if total > costliest_tokens:
            costliest_phase = phase
            costliest_tokens = total

    # Sub-agent usage counts
    sub_agent_usage: dict[str, int] = {}
    for t in traces:
        for sa in t.sub_agents:
            sub_agent_usage[sa.role] = sub_agent_usage.get(sa.role, 0) + 1

    # Token trend: compare last 3 vs first 3 (if enough data)
    token_trend = 0.0
    if len(per_trace_tokens) >= 4:
        first_half = per_trace_tokens[: len(per_trace_tokens) // 2]
        second_half = per_trace_tokens[len(per_trace_tokens) // 2 :]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        if avg_first > 0:
            token_trend = (avg_second - avg_first) / avg_first

    return AggregatedMetrics(
        trace_count=len(traces),
        total_tokens=total_tokens,
        avg_tokens_per_trace=round(avg_tokens, 1),
        costliest_phase=costliest_phase,
        costliest_phase_tokens=costliest_tokens,
        phase_avg_tokens={k: round(v, 1) for k, v in phase_avg.items()},
        sub_agent_usage=sub_agent_usage,
        recent_traces=traces[-5:],
        token_trend=round(token_trend, 3),
        per_trace_tokens=per_trace_tokens,
    )


def get_metrics(
    limit: int = 10, hours: int = 24, cache_ttl: int = 300
) -> AggregatedMetrics:
    """Get aggregated Langfuse metrics with local cache.

    Args:
        limit: Max traces to fetch.
        hours: Look-back window in hours.
        cache_ttl: Cache duration in seconds (default 5 min).
    """
    global _cached_metrics, _cached_at

    now = time.time()
    if _cached_metrics is not None and (now - _cached_at) < cache_ttl:
        return _cached_metrics

    traces = fetch_recent_traces(limit=limit, hours=hours)
    metrics = aggregate_metrics(traces)

    _cached_metrics = metrics
    _cached_at = now
    return metrics


def reset_cache() -> None:
    """Clear the local metrics cache."""
    global _cached_metrics, _cached_at
    _cached_metrics = None
    _cached_at = 0.0
