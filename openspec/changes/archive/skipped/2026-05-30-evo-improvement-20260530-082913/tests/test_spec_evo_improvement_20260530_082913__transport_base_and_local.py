"""Tests for spec: transport-base-and-local

Covers Transport base class interface and LocalTransport subprocess delegation.
"""
from unittest.mock import patch, MagicMock

import pytest

from zsiga.transport import Transport, LocalTransport


# ---------------------------------------------------------------------------
# Transport.run_shell raises NotImplementedError
# ---------------------------------------------------------------------------
def test_run_shell_raises_not_implemented():
    """Transport.run_shell raises NotImplementedError."""
    t = Transport()
    with pytest.raises(NotImplementedError):
        t.run_shell("echo hi")


# ---------------------------------------------------------------------------
# Transport.close returns None without error
# ---------------------------------------------------------------------------
def test_close_returns_none():
    """Transport.close returns None without error."""
    t = Transport()
    result = t.close()
    assert result is None


# ---------------------------------------------------------------------------
# LocalTransport.run_shell returns structured result
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_local_run_shell_returns_structured_result(mock_run):
    """LocalTransport.run_shell returns dict with exit_code, stdout, stderr."""
    mock_run.return_value = MagicMock(returncode=0, stdout="hello\n", stderr="")
    t = LocalTransport()
    result = t.run_shell("echo hello")
    assert result == {"exit_code": 0, "stdout": "hello\n", "stderr": ""}


# ---------------------------------------------------------------------------
# LocalTransport.run_shell passes cwd to subprocess
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_local_run_shell_passes_cwd(mock_run):
    """LocalTransport.run_shell passes cwd kwarg to subprocess.run."""
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    t = LocalTransport()
    t.run_shell("ls", cwd="/tmp")
    _, kwargs = mock_run.call_args
    assert kwargs["cwd"] == "/tmp"


# ---------------------------------------------------------------------------
# LocalTransport.run_shell passes stdin_data to subprocess
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_local_run_shell_passes_stdin_data(mock_run):
    """LocalTransport.run_shell passes stdin_data as input to subprocess.run."""
    mock_run.return_value = MagicMock(returncode=0, stdout="hello", stderr="")
    t = LocalTransport()
    t.run_shell("cat", stdin_data="hello")
    _, kwargs = mock_run.call_args
    assert kwargs["input"] == "hello"


# ---------------------------------------------------------------------------
# LocalTransport.run_shell respects timeout parameter
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_local_run_shell_respects_timeout(mock_run):
    """LocalTransport.run_shell passes timeout kwarg to subprocess.run."""
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    t = LocalTransport()
    t.run_shell("sleep 5", timeout=30)
    _, kwargs = mock_run.call_args
    assert kwargs["timeout"] == 30
