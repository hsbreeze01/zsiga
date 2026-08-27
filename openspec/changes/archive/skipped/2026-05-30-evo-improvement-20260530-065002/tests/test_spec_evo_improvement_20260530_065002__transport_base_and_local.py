"""Tests for transport-base-and-local.md spec scenarios.

Covers: Transport base class, LocalTransport.run_shell
"""
from unittest.mock import MagicMock, patch

from zsiga.transport import LocalTransport, Transport


class TestTransportBaseClass:
    """Spec: Transport base class abstract contract."""

    def test_base_run_shell_raises_not_implemented(self):
        """Scenario: Base Transport.run_shell raises NotImplementedError."""
        t = Transport()
        raised = False
        try:
            t.run_shell("echo hi")
        except NotImplementedError:
            raised = True
        assert raised, "Expected NotImplementedError from Transport.run_shell"

    def test_base_close_returns_none(self):
        """Scenario: Base Transport.close returns None."""
        t = Transport()
        result = t.close()
        assert result is None


class TestLocalTransportRunShell:
    """Spec: LocalTransport.run_shell delegates to subprocess."""

    @patch("zsiga.transport.subprocess.run")
    def test_returns_subprocess_result(self, mock_run):
        """Scenario: LocalTransport.run_shell returns subprocess result."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
        t = LocalTransport()
        result = t.run_shell("echo ok")
        assert result == {"exit_code": 0, "stdout": "ok\n", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_passes_cwd_timeout_stdin_to_subprocess(self, mock_run):
        """Scenario: LocalTransport.run_shell passes cwd and timeout to subprocess."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        t = LocalTransport()
        t.run_shell("ls", cwd="/tmp", timeout=30, stdin_data="data")
        mock_run.assert_called_once_with(
            "ls",
            shell=True,
            cwd="/tmp",
            capture_output=True,
            text=True,
            timeout=30,
            input="data",
        )

    @patch("zsiga.transport.subprocess.run")
    def test_captures_non_zero_exit_code(self, mock_run):
        """Scenario: LocalTransport.run_shell captures non-zero exit code."""
        mock_run.return_value = MagicMock(
            returncode=127, stdout="", stderr="command not found"
        )
        t = LocalTransport()
        result = t.run_shell("badcmd")
        assert result == {
            "exit_code": 127,
            "stdout": "",
            "stderr": "command not found",
        }
