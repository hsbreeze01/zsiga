"""Spec tests for transport base class and LocalTransport.

Covers specs: transport-base-and-local.md
"""
from unittest.mock import MagicMock, patch

import pytest

from zsiga.transport import LocalTransport, Transport


class TestTransportBaseClass:
    """Transport base class contract."""

    def test_run_shell_raises_not_implemented_error(self):
        """Scenario: Transport.run_shell raises NotImplementedError."""
        t = Transport()
        with pytest.raises(NotImplementedError):
            t.run_shell("echo hi")

    def test_close_is_noop(self):
        """Scenario: Transport.close is a no-op."""
        t = Transport()
        # Should not raise
        t.close()


class TestLocalTransport:
    """LocalTransport.run_shell delegates to subprocess."""

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_returns_dict_from_subprocess(self, mock_run):
        """Scenario: LocalTransport.run_shell returns dict from subprocess."""
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = "ok"
        proc.stderr = ""
        mock_run.return_value = proc

        lt = LocalTransport()
        result = lt.run_shell("echo ok")

        assert result == {"exit_code": 0, "stdout": "ok", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_forwards_cwd_and_timeout(self, mock_run):
        """Scenario: LocalTransport.run_shell forwards cwd and timeout."""
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = ""
        proc.stderr = ""
        mock_run.return_value = proc

        lt = LocalTransport()
        lt.run_shell("ls", cwd="/tmp", timeout=30)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("cwd") == "/tmp" or call_kwargs[1].get("cwd") == "/tmp"
        # Check positional or keyword
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 30
        assert kwargs["cwd"] == "/tmp"

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_forwards_stdin_data_as_input(self, mock_run):
        """Scenario: LocalTransport.run_shell forwards stdin_data as input."""
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = ""
        proc.stderr = ""
        mock_run.return_value = proc

        lt = LocalTransport()
        lt.run_shell("cat", stdin_data="hello")

        _, kwargs = mock_run.call_args
        assert kwargs["input"] == "hello"
