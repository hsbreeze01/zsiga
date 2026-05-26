"""Token budget tracker for agent loop sessions."""

from ..agent.intent_router import IntentType


class TokenBudget:
    """Tracks cumulative token usage and enforces budget limits.

    Parameters
    ----------
    total_budget : int
        Maximum total tokens (prompt + completion) per session.
    per_turn_limit : int
        Maximum completion tokens allowed in a single LLM call.
    compaction_threshold : int
        Token threshold used by the compaction subsystem.
    compaction_ratio : float
        Fraction of *compaction_threshold* at which proactive compaction
        is triggered (default 0.8).
    stale_limit : int
        Consecutive stale turns before stopping (default 5).
    budget_extend_factor : float
        Multiplier for soft budget extension when producing value (default 1.5).
    """

    def __init__(
        self,
        total_budget: int = 600000,
        per_turn_limit: int = 8192,
        compaction_threshold: int = 60000,
        compaction_ratio: float = 0.8,
        stale_limit: int = 10,
        budget_extend_factor: float = 1.5,
    ):
        self.total_budget = total_budget
        self.per_turn_limit = per_turn_limit
        self.compaction_threshold = compaction_threshold
        self.compaction_ratio = compaction_ratio
        self.stale_limit = stale_limit
        self.budget_extend_factor = budget_extend_factor
        self._used: int = 0
        self._consecutive_stale: int = 0
        self._extended: bool = False

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def record(self, prompt_tokens: int, completion_tokens: int,
               value_signal: str | None = None) -> dict:
        """Record usage from one LLM call.

        Parameters
        ----------
        prompt_tokens, completion_tokens : int
            Token counts from the LLM response.
        value_signal : str or None
            ``"productive"`` or ``"stale"`` from ValueTracker.  When
            provided the method returns additional keys.

        Returns
        -------
        dict
            Always: ``session_exceeded``, ``turn_exceeded``, ``used``,
            ``remaining``.  When *value_signal* is given: also
            ``stale_count``, ``effective_budget``, ``should_stop``.
        """
        self._used += prompt_tokens + completion_tokens

        turn_exceeded = completion_tokens > self.per_turn_limit

        # Value-signal tracking
        if value_signal is not None:
            if value_signal == "productive":
                self._consecutive_stale = 0
            else:
                self._consecutive_stale += 1

        eff = self.effective_budget
        session_exceeded = self._used > eff

        result: dict = {
            "session_exceeded": session_exceeded,
            "turn_exceeded": turn_exceeded,
            "used": self._used,
            "remaining": eff - self._used,
        }

        if value_signal is not None:
            result["stale_count"] = self._consecutive_stale
            result["effective_budget"] = eff
            result["should_stop"] = (
                self._consecutive_stale >= self.stale_limit
            ) or session_exceeded

        return result

    @property
    def effective_budget(self) -> int:
        """Return the current effective budget, accounting for soft extension."""
        if self._extended:
            return int(self.total_budget * self.budget_extend_factor)
        return self.total_budget

    def try_extend(self, value_signal: str) -> bool:
        """Attempt a soft budget extension.

        Extends to ``min(total_budget * factor, total_budget + margin)``
        when *value_signal* is ``"productive"`` and the session has
        exceeded the original budget.  The effective budget is capped at
        ``total_budget * budget_extend_factor``.

        Returns ``True`` if the budget was extended.
        """
        if self._extended:
            return False
        if value_signal != "productive":
            return False
        if self._used > self.total_budget:
            self._extended = True
            return True
        return False

    def should_compact(self, messages, estimate_fn) -> bool:
        """Return ``True`` when estimated tokens >= threshold * ratio."""
        estimated = estimate_fn(messages)
        return estimated >= self.compaction_threshold * self.compaction_ratio

    def reset(self):
        """Reset usage counters so the next phase starts with a fresh budget."""
        self._used = 0
        self._consecutive_stale = 0
        self._extended = False

    def snapshot(self) -> dict:
        """Return current budget state for logging / dashboard."""
        eff = self.effective_budget
        return {
            "total_budget": self.total_budget,
            "used": self._used,
            "remaining": eff - self._used,
            "usage_ratio": self._used / eff if eff else 0.0,
            "effective_budget": eff,
            "extended": self._extended,
            "consecutive_stale": self._consecutive_stale,
        }
