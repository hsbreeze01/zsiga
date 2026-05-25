"""Langfuse instrumentation shim — feature-flagged, no-ops when keys absent.

Why a shim instead of using ``@observe`` directly:

- Zsiga's pipeline mixes ``async`` (orchestrator phases) with sync LLM calls
  dispatched into an executor thread. We need the trace span to live on the
  main async thread (so parent context propagates), with the LLM call
  running synchronously inside; the @observe decorator can't cleanly
  bridge that.
- We want a single import surface so daemon / orchestrator / loop don't
  have to each handle the "Langfuse not configured" case.
- Future: easy to add custom score / evaluator hooks here without
  scattering ``client.score(...)`` calls across the pipeline.

API:

    from .langfuse_shim import (
        is_enabled,
        trace_proposal,
        phase_span,
        llm_generation,
        flush,
    )

    with trace_proposal(change_name=name, project=project) as t:
        with phase_span("clarify"):
            ...
        with phase_span("implement"):
            with llm_generation("turn-0", model="glm-5.1") as gen:
                resp = await llm_call(...)
                if gen:
                    gen.update(
                        output=resp.choices[0].message.content,
                        usage_details={"input": ..., "output": ...},
                    )

When ``LANGFUSE_PUBLIC_KEY`` / ``LANGFUSE_SECRET_KEY`` are unset, every
context manager yields ``None`` immediately — zero overhead beyond the
env-var check.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator

log = logging.getLogger(__name__)

_enabled_cache: bool | None = None
_client_cache: Any | None = None


def is_enabled() -> bool:
    """Return True iff Langfuse env vars are set.

    Cached on first call. To re-evaluate (e.g. after env-file reload),
    call :func:`reset_cache`.
    """
    global _enabled_cache
    if _enabled_cache is None:
        _enabled_cache = bool(
            os.environ.get("LANGFUSE_PUBLIC_KEY")
            and os.environ.get("LANGFUSE_SECRET_KEY")
        )
    return _enabled_cache


def reset_cache() -> None:
    """Reset cached enabled flag + client; call after .env reload."""
    global _enabled_cache, _client_cache
    _enabled_cache = None
    if _client_cache is not None:
        try:
            _client_cache.flush()
        except Exception:
            pass
        _client_cache = None


def _client():
    """Lazy-init Langfuse client. Returns None when disabled or import fails."""
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    if not is_enabled():
        return None
    try:
        from langfuse import Langfuse
        _client_cache = Langfuse()
    except Exception as exc:  # pragma: no cover - defensive, never block daemon
        log.warning("Langfuse client init failed: %s", exc)
        _client_cache = None
    return _client_cache


@contextmanager
def trace_proposal(
    change_name: str,
    project: str = "zsiga",
    intent: str | None = None,
    **metadata: Any,
) -> Iterator[Any | None]:
    """Top-level trace span for one proposal × cycle execution.

    Establishes session_id = change_name + tags = [project, manual|auto]
    so the LangFuse UI groups runs of the same proposal under one
    session, and lets the project / intent / change-name dimensions
    drive filtering.
    """
    client = _client()
    if client is None:
        yield None
        return
    try:
        from langfuse import propagate_attributes
    except Exception:  # pragma: no cover
        yield None
        return

    is_auto = change_name.startswith("auto-")
    tags = [project, "auto" if is_auto else "manual"]
    if intent:
        tags.append(f"intent:{intent}")

    base_metadata = {
        "change_name": change_name,
        "project": project,
        "is_auto": str(is_auto),
    }
    if intent:
        base_metadata["intent"] = intent
    base_metadata.update(metadata)

    span = None
    cm_obs = None
    cm_prop = None
    try:
        cm_obs = client.start_as_current_observation(
            name=f"proposal:{change_name}",
            as_type="span",
            input=base_metadata,
        )
        span = cm_obs.__enter__()
        cm_prop = propagate_attributes(
            session_id=change_name,
            user_id=project,
            tags=tags,
            metadata=base_metadata,
            trace_name=change_name,
        )
        cm_prop.__enter__()
        yield span
    except Exception as exc:
        log.warning("Langfuse trace_proposal error: %s", exc)
        yield None
    finally:
        if cm_prop is not None:
            try:
                cm_prop.__exit__(None, None, None)
            except Exception:
                pass
        if cm_obs is not None:
            try:
                cm_obs.__exit__(None, None, None)
            except Exception:
                pass


@contextmanager
def phase_span(
    phase_name: str,
    change_name: str = "",
    **metadata: Any,
) -> Iterator[Any | None]:
    """Span for a single pipeline phase (clarify / enrich / implement / ...)."""
    client = _client()
    if client is None:
        yield None
        return
    payload = {"phase": phase_name}
    if change_name:
        payload["change_name"] = change_name
    payload.update(metadata)
    span = None
    try:
        cm = client.start_as_current_observation(
            name=f"phase:{phase_name}",
            as_type="span",
            metadata=payload,
        )
        span = cm.__enter__()
        yield span
    except Exception as exc:
        log.warning("Langfuse phase_span error: %s", exc)
        yield None
    finally:
        if span is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass


@contextmanager
def sub_agent_span(
    role: str,
    parent_phase: str = "",
    **metadata: Any,
) -> Iterator[Any | None]:
    """Span for a sub-agent (review / explore / implement / verify) run."""
    client = _client()
    if client is None:
        yield None
        return
    payload = {"role": role}
    if parent_phase:
        payload["parent_phase"] = parent_phase
    payload.update(metadata)
    span = None
    try:
        cm = client.start_as_current_observation(
            name=f"sub_agent:{role}",
            as_type="agent",
            metadata=payload,
        )
        span = cm.__enter__()
        yield span
    except Exception as exc:
        log.warning("Langfuse sub_agent_span error: %s", exc)
        yield None
    finally:
        if span is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass


@contextmanager
def llm_generation(
    name: str,
    model: str,
    provider: str = "",
    **metadata: Any,
) -> Iterator[Any | None]:
    """Generation span for one LLM call.

    Caller is expected to call ``gen.update(output=..., usage_details=...,
    input=..., model_parameters=...)`` after the response is available.
    """
    client = _client()
    if client is None:
        yield None
        return
    payload = {"provider": provider} if provider else {}
    payload.update(metadata)
    gen = None
    cm = None
    try:
        cm = client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            metadata=payload,
        )
        gen = cm.__enter__()
        yield gen
    except Exception as exc:
        log.warning("Langfuse llm_generation error: %s", exc)
        yield None
    finally:
        if cm is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass


def flush() -> None:
    """Flush pending events. Call on daemon shutdown."""
    if _client_cache is not None:
        try:
            _client_cache.flush()
        except Exception as exc:  # pragma: no cover
            log.warning("Langfuse flush error: %s", exc)


def update_current_observation(**kwargs: Any) -> None:
    """Convenience wrapper around ``client.update_current_observation``.

    Useful in deep call sites where the span object isn't held directly.
    """
    client = _client()
    if client is None:
        return
    try:
        # SDK exposes both update_current_span and update_current_generation;
        # we call the generic one based on observation type.
        client.update_current_observation(**kwargs)
    except Exception as exc:  # pragma: no cover
        log.warning("Langfuse update_current_observation error: %s", exc)
