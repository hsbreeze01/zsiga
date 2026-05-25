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

OTel context bug: Langfuse SDK wraps OTel's _AgnosticContextManager which
uses ContextVar tokens internally.  In zsiga's async + thread-pool
environment, ``detach(token)`` routinely raises ``ValueError: token was
created in a different Context``.  We suppress all such errors in
``_safe_exit`` — Langfuse traces are best-effort observability and must
never block the pipeline.

API:

    from .langfuse_shim import (
        is_enabled,
        trace_proposal,
        phase_span,
        sub_agent_span,
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
    global _enabled_cache
    if _enabled_cache is None:
        _enabled_cache = bool(
            os.environ.get("LANGFUSE_PUBLIC_KEY")
            and os.environ.get("LANGFUSE_SECRET_KEY")
        )
    return _enabled_cache


def reset_cache() -> None:
    global _enabled_cache, _client_cache
    _enabled_cache = None
    if _client_cache is not None:
        try:
            _client_cache.flush()
        except Exception:
            pass
        _client_cache = None


def _client():
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    if not is_enabled():
        return None
    try:
        from langfuse import Langfuse
        _client_cache = Langfuse()
    except Exception as exc:
        log.warning("Langfuse client init failed: %s", exc)
        _client_cache = None
    return _client_cache


def _safe_exit(cm: Any) -> None:
    """Call ``cm.__exit__(None, None, None)`` suppressing all errors.

    OTel's ``_AgnosticContextManager.__exit__`` raises ``ValueError``
    when its internal ``ContextVar`` token was created in a different
    async context — which happens routinely in zsiga's mixed
    async / thread-pool environment.  Suppressing is safe because
    Langfuse traces are purely best-effort observability.
    """
    if cm is None:
        return
    try:
        cm.__exit__(None, None, None)
    except Exception:
        pass


@contextmanager
def _observation_span(
    build_cm: Any,
) -> Iterator[Any | None]:
    """Shared pattern: manually enter/exit an OTel context manager.

    Using ``with`` directly causes ``GeneratorExit`` during ``__exit__``
    which corrupts the ``@contextmanager`` generator (double-yield).
    Manual ``__enter__``/``__exit__`` via ``_safe_exit`` avoids this.
    """
    cm = None
    try:
        cm = build_cm()
        span = cm.__enter__()
        yield span
    except GeneratorExit:
        _safe_exit(cm)
        raise
    except Exception:
        _safe_exit(cm)
        yield None
        return
    finally:
        _safe_exit(cm)


@contextmanager
def trace_proposal(
    change_name: str,
    project: str = "zsiga",
    intent: str | None = None,
    **metadata: Any,
) -> Iterator[Any | None]:
    client = _client()
    if client is None:
        yield None
        return

    is_auto = change_name.startswith("auto-")
    tags = [project, "auto" if is_auto else "manual"]
    if intent:
        tags.append(f"intent:{intent}")

    base_metadata: dict[str, Any] = {
        "change_name": change_name,
        "project": project,
        "is_auto": str(is_auto),
    }
    if intent:
        base_metadata["intent"] = intent
    base_metadata.update(metadata)

    with _observation_span(
        lambda: client.start_as_current_observation(
            name=f"proposal:{change_name}",
            as_type="span",
            input=base_metadata,
        ),
    ) as span:
        yield span


@contextmanager
def phase_span(
    phase_name: str,
    change_name: str = "",
    **metadata: Any,
) -> Iterator[Any | None]:
    client = _client()
    if client is None:
        yield None
        return
    payload: dict[str, Any] = {"phase": phase_name}
    if change_name:
        payload["change_name"] = change_name
    payload.update(metadata)

    with _observation_span(
        lambda: client.start_as_current_observation(
            name=f"phase:{phase_name}",
            as_type="span",
            metadata=payload,
        ),
    ) as span:
        yield span


@contextmanager
def sub_agent_span(
    role: str,
    parent_phase: str = "",
    **metadata: Any,
) -> Iterator[Any | None]:
    client = _client()
    if client is None:
        yield None
        return
    payload: dict[str, Any] = {"role": role}
    if parent_phase:
        payload["parent_phase"] = parent_phase
    payload.update(metadata)

    with _observation_span(
        lambda: client.start_as_current_observation(
            name=f"sub_agent:{role}",
            as_type="agent",
            metadata=payload,
        ),
    ) as span:
        yield span


@contextmanager
def llm_generation(
    name: str,
    model: str,
    provider: str = "",
    **metadata: Any,
) -> Iterator[Any | None]:
    client = _client()
    if client is None:
        yield None
        return
    payload: dict[str, Any] = {"provider": provider} if provider else {}
    payload.update(metadata)

    with _observation_span(
        lambda: client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            metadata=payload,
        ),
    ) as gen:
        yield gen


def flush() -> None:
    if _client_cache is not None:
        try:
            _client_cache.flush()
        except Exception as exc:
            log.warning("Langfuse flush error: %s", exc)


def update_current_observation(**kwargs: Any) -> None:
    client = _client()
    if client is None:
        return
    try:
        client.update_current_observation(**kwargs)
    except Exception as exc:
        log.warning("Langfuse update_current_observation error: %s", exc)
