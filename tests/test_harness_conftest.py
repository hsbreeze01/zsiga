"""Tests for zsiga.harness.conftest — mock fixtures."""

from __future__ import annotations

from pathlib import Path

from zsiga.harness.conftest import (
    MockLLMClient,
    MockTransport,
    TempGitRepo,
    mock_llm_client,
    mock_transport,
    temp_git_repo,
)


# ---------------------------------------------------------------------------
# MockLLMClient
# ---------------------------------------------------------------------------


class TestMockLLMClient:
    """Verify MockLLMClient response, configuration, and call recording."""

    def test_default_response(self) -> None:
        client = MockLLMClient()
        assert client.chat("hello") == "mock response"

    def test_set_response(self) -> None:
        client = MockLLMClient()
        client.set_response("custom reply")
        assert client.chat("hello") == "custom reply"

    def test_call_recording(self) -> None:
        client = MockLLMClient()
        client.chat("first")
        client.chat("second")
        assert client.calls == [("first",), ("second",)]

    def test_set_response_changes_subsequent(self) -> None:
        client = MockLLMClient()
        assert client.chat("a") == "mock response"
        client.set_response("new reply")
        assert client.chat("b") == "new reply"
        assert len(client.calls) == 2

    def test_factory_returns_instance(self) -> None:
        client = mock_llm_client()
        assert isinstance(client, MockLLMClient)


# ---------------------------------------------------------------------------
# MockTransport
# ---------------------------------------------------------------------------


class TestMockTransport:
    """Verify MockTransport call recording and configurable results."""

    def test_default_result(self) -> None:
        transport = MockTransport()
        result = transport.call("read_file", {"path": "/tmp/x"})
        assert result == {"ok": True}

    def test_call_recording(self) -> None:
        transport = MockTransport()
        transport.call("read_file", {"path": "/tmp/x"})
        transport.call("write_file", {"path": "/tmp/y", "content": "hi"})
        assert transport.recorded == [
            ("read_file", {"path": "/tmp/x"}),
            ("write_file", {"path": "/tmp/y", "content": "hi"}),
        ]

    def test_set_result(self) -> None:
        transport = MockTransport()
        transport.set_result({"status": "done"})
        assert transport.call("any", {}) == {"status": "done"}

    def test_no_real_io(self) -> None:
        """Transport.call should not perform any real I/O."""
        transport = MockTransport()
        # Calling with arbitrary tool names should never raise IO errors
        transport.call("dangerous_tool", {"anything": True})

    def test_factory_returns_instance(self) -> None:
        transport = mock_transport()
        assert isinstance(transport, MockTransport)


# ---------------------------------------------------------------------------
# TempGitRepo
# ---------------------------------------------------------------------------


class TestTempGitRepo:
    """Verify TempGitRepo creation, cleanup, and initial commit."""

    def test_creates_git_repo(self) -> None:
        repo = TempGitRepo()
        assert (repo.path / ".git").is_dir()
        assert repo.path.is_dir()
        repo.cleanup()

    def test_path_is_writable(self, tmp_path: Path) -> None:
        repo = TempGitRepo()
        test_file = repo.path / "test.txt"
        test_file.write_text("hello")
        assert test_file.read_text() == "hello"
        repo.cleanup()

    def test_cleanup_removes_directory(self) -> None:
        repo = TempGitRepo()
        path = repo.path
        assert path.exists()
        repo.cleanup()
        assert not path.exists()

    def test_initial_commit(self) -> None:
        repo = TempGitRepo(initial_commit=True)
        result = repo.git("log", "--oneline")
        assert b"initial commit" in result.stdout
        repo.cleanup()

    def test_initial_commit_has_readme(self) -> None:
        repo = TempGitRepo(initial_commit=True)
        assert (repo.path / "README.md").exists()
        repo.cleanup()

    def test_no_initial_commit_by_default(self) -> None:
        repo = TempGitRepo()
        result = repo.git("log", "--oneline")
        # No commits yet — log should fail or be empty
        assert result.returncode != 0 or result.stdout.strip() == b""
        repo.cleanup()

    def test_git_command_works(self) -> None:
        repo = TempGitRepo()
        result = repo.git("status")
        assert result.returncode == 0
        repo.cleanup()

    def test_factory_returns_instance(self) -> None:
        repo = temp_git_repo()
        assert isinstance(repo, TempGitRepo)
        repo.cleanup()

    def test_factory_with_initial_commit(self) -> None:
        repo = temp_git_repo(initial_commit=True)
        result = repo.git("log", "--oneline")
        assert b"initial commit" in result.stdout
        repo.cleanup()
