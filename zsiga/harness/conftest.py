"""Mock fixtures for zsiga test harness."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any


class MockLLMClient:
    """Deterministic mock of the LLM client used by zsiga.

    Records all calls and returns configurable canned responses.
    """

    def __init__(self) -> None:
        self._response: str = "mock response"
        self.calls: list[tuple[str, ...]] = []

    def chat(self, prompt: str) -> str:
        """Return a deterministic response and record the call."""
        self.calls.append((prompt,))
        return self._response

    def set_response(self, text: str) -> None:
        """Configure the response returned by subsequent chat() calls."""
        self._response = text


class MockTransport:
    """Simulates the tool-execution transport layer without real side effects.

    Records all calls and returns configurable default results.
    """

    def __init__(self) -> None:
        self._result: dict[str, Any] = {"ok": True}
        self.recorded: list[tuple[str, dict[str, Any]]] = []

    def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Record the call and return the configured default result.

        Performs no real I/O.
        """
        self.recorded.append((tool_name, args))
        return self._result

    def set_result(self, result: dict[str, Any]) -> None:
        """Configure the result returned by subsequent call() invocations."""
        self._result = result


class TempGitRepo:
    """Isolated temporary git repository, cleaned up after use."""

    def __init__(self, initial_commit: bool = False) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="zsiga_harness_")
        self.path = Path(self._tmpdir)
        subprocess.run(
            ["git", "init"], cwd=self.path, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@zsiga.dev"],
            cwd=self.path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "zsiga test"],
            cwd=self.path,
            capture_output=True,
            check=True,
        )
        if initial_commit:
            (self.path / "README.md").write_text("# test repo\n")
            subprocess.run(
                ["git", "add", "README.md"],
                cwd=self.path,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "initial commit"],
                cwd=self.path,
                capture_output=True,
                check=True,
            )

    def git(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        """Run a git command in the repo and return the result."""
        return subprocess.run(
            ["git", *args], cwd=self.path, capture_output=True,
        )

    def cleanup(self) -> None:
        """Remove the temporary directory tree."""
        import shutil

        if self.path.exists():
            shutil.rmtree(self.path)

    def __del__(self) -> None:
        try:
            self.cleanup()
        except Exception:
            pass


# --- Factory functions (return fresh instances) ---


def mock_llm_client() -> MockLLMClient:
    """Return a fresh MockLLMClient instance."""
    return MockLLMClient()


def mock_transport() -> MockTransport:
    """Return a fresh MockTransport instance."""
    return MockTransport()


def temp_git_repo(initial_commit: bool = False) -> TempGitRepo:
    """Return a fresh TempGitRepo instance.

    Args:
        initial_commit: If True, create an initial commit on the default branch.
    """
    return TempGitRepo(initial_commit=initial_commit)
