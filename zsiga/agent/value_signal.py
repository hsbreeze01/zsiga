"""Value-signal detection for budget-aware agent loop."""

from __future__ import annotations

# Tool names that indicate a productive turn (file writes).
_FILE_WRITE_TOOLS = frozenset({"write_file", "edit_file"})

# Substrings in bash commands that indicate a test or lint invocation.
_TEST_PATTERNS = ("pytest", "test", "unittest", "nosetests")
_LINT_PATTERNS = ("ruff", "flake8", "pylint", "mypy", "eslint")


def classify_turn(tool_names: list[str], tool_results: list[dict]) -> str:
    """Classify a completed turn as ``"productive"`` or ``"stale"``.

    A turn is **productive** if ANY of:
    - ``write_file`` or ``edit_file`` in *tool_names*
    - A bash tool returned ``exit_code`` 0 for a test command
    - A bash tool returned ``exit_code`` 0 for a lint command
    - A task was checked off (``edit_file`` on tasks.md with ``- [x]``)

    Otherwise the turn is **stale**.

    Parameters
    ----------
    tool_names:
        List of tool function names invoked during the turn.
    tool_results:
        Corresponding list of result dicts from those tool calls.
        Each may contain ``exit_code`` (int) and ``stdout`` / ``command``
        keys when the tool was a bash invocation.

    Returns
    -------
    str
        ``"productive"`` or ``"stale"``
    """
    # Any file-write tool → productive
    for name in tool_names:
        if name in _FILE_WRITE_TOOLS:
            return "productive"

    # Check bash results for test/lint success
    for name, result in zip(tool_names, tool_results):
        if name != "bash":
            continue
        if not isinstance(result, dict):
            continue
        exit_code = result.get("exit_code")
        if exit_code != 0:
            continue
        stdout = result.get("stdout", "") or ""
        command = result.get("command", "") or ""
        combined = command + " " + stdout
        for pat in _TEST_PATTERNS:
            if pat in combined:
                return "productive"
        for pat in _LINT_PATTERNS:
            if pat in combined:
                return "productive"

    return "stale"


class ValueTracker:
    """Tracks consecutive stale count and records turn classifications."""

    def __init__(self, stale_limit: int = 5):
        self.stale_limit = stale_limit
        self._consecutive_stale: int = 0

    @property
    def stale_count(self) -> int:
        return self._consecutive_stale

    def record_turn(self, classification: str) -> dict:
        """Record a turn classification and return status.

        Parameters
        ----------
        classification:
            ``"productive"`` or ``"stale"``

        Returns
        -------
        dict
            ``stale_count``, ``value_signal``, ``limit_reached``
        """
        if classification == "productive":
            self._consecutive_stale = 0
        else:
            self._consecutive_stale += 1

        return {
            "stale_count": self._consecutive_stale,
            "value_signal": classification,
            "limit_reached": self._consecutive_stale >= self.stale_limit,
        }

    def reset(self) -> None:
        """Reset the consecutive stale counter."""
        self._consecutive_stale = 0
