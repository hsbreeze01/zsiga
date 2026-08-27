"""Tests for transport-base-and-local spec.

Covers Transport base class and LocalTransport.run_shell.
"""
from unittest.mock import MagicMock, patch

import pytest

from zsiga.transport import LocalTransport, Transport


# ── Transport base class ────────────────────────────────────────────


class TestTransportBase:
    def test_transport_run_shell_raises_not_implemented(self):
        """Scenario: Transport.run_shell raises NotImplementedError"""
        t = Transport()
        with pytest.raises(NotImplementedError):
            t.run_shell("echo hi")

    def test_transport_close_is_noop(self):
        """Scenario: Transport.close is a no-op"""
        t = Transport()
        # Should not raise
        t.close()


# ── LocalTransport ──────────────────────────────────────────────────


class TestLocalTransportRunShell:
    @patch("zsiga.transport.subprocess.run")
    def test_returns_structured_result(self, mock_run):
        """Scenario: LocalTransport.run_shell returns structured result"""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        lt = LocalTransport()
        result = lt.run_shell("echo ok")
        assert result == {"exit_code": 0, "stdout": "ok", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_cwd(self, mock_run):
        """Scenario: LocalTransport.run_shell forwards cwd parameter"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        lt = LocalTransport()
        lt.run_shell("ls", cwd="/tmp")
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == "/tmp"

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_timeout(self, mock_run):
        """Scenario: LocalTransport.run_shell forwards timeout parameter"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        lt = LocalTransport()
        lt.run_shell("ls", timeout=30)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 30

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_stdin_data(self, mock_run):
        """Scenario: LocalTransport.run_shell forwards stdin_data parameter"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        lt = LocalTransport()
        lt.run_shell("cat", stdin_data="hello")
        _, kwargs = mock_run.call_args
        assert kwargs["input"] == "hello"

    @patch("zsiga.transport.subprocess.run")
    def test_calls_subprocess_with_shell_true(self, mock_run):
        """Scenario: LocalTransport.run_shell calls subprocess with shell=True"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        lt = LocalTransport()
        lt.run_shell("echo hi")
        _, kwargs = mock_run.call_args
        assert kwargs["shell"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True

    @patch("zsiga.transport.subprocess.run")
    def test_propagates_nonzero_exit_code(self, mock_run):
        """Scenario: LocalTransport.run_shell propagates nonzero exit code"""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="fail")
        lt = LocalTransport()
        result = lt.run_shell("false")
        assert result == {"exit_code": 1, "stdout": "", "stderr": "fail"}
