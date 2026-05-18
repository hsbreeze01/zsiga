"""Token budget tracker for agent loop sessions."""


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
    """

    def __init__(
        self,
        total_budget: int = 400000,
        per_turn_limit: int = 8192,
        compaction_threshold: int = 60000,
        compaction_ratio: float = 0.8,
    ):
        self.total_budget = total_budget
        self.per_turn_limit = per_turn_limit
        self.compaction_threshold = compaction_threshold
        self.compaction_ratio = compaction_ratio
        self._used: int = 0

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def record(self, prompt_tokens: int, completion_tokens: int) -> dict:
        """Record usage from one LLM call.

        Returns a status dict with keys:
        - ``session_exceeded`` (bool)
        - ``turn_exceeded`` (bool)
        - ``used`` (int, cumulative)
        - ``remaining`` (int)
        """
        self._used += prompt_tokens + completion_tokens

        turn_exceeded = completion_tokens > self.per_turn_limit
        session_exceeded = self._used > self.total_budget

        return {
            "session_exceeded": session_exceeded,
            "turn_exceeded": turn_exceeded,
            "used": self._used,
            "remaining": self.total_budget - self._used,
        }

    def should_compact(self, messages, estimate_fn) -> bool:
        """Return ``True`` when estimated tokens >= threshold * ratio."""
        estimated = estimate_fn(messages)
        return estimated >= self.compaction_threshold * self.compaction_ratio

    def snapshot(self) -> dict:
        """Return current budget state for logging / dashboard."""
        return {
            "total_budget": self.total_budget,
            "used": self._used,
            "remaining": self.total_budget - self._used,
            "usage_ratio": self._used / self.total_budget if self.total_budget else 0.0,
        }
