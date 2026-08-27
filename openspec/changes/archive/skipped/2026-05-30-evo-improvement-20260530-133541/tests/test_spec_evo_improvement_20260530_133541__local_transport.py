"""Tests for local-transport spec — LocalTransport command execution."""
from unittest.mock import patch, MagicMock

from zsiga.transport import LocalTransport


def test_successful_command_returns_exit_code_0_and_stdout():
    """Successful command returns exit_code 0 and captured stdout."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ok\n"
    mock_result.stderr = ""

    with patch("zsiga.transport.subprocess.run", return_value=mock_result):
        lt = LocalTransport()
        result = lt.run_shell("echo ok")

    assert result == {"exit_code": 0, "stdout": "ok\n", "stderr": ""}


def test_failed_command_returns_nonzero_exit_code_and_stderr():
    """Failed command returns non-zero exit_code and stderr."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error"

    with patch("zsiga.transport.subprocess.run", return_value=mock_result):
        lt = LocalTransport()
        result = lt.run_shell("false")

    assert result == {"exit_code": 1, "stdout": "", "stderr": "error"}


def test_run_shell_passes_cwd_to_subprocess():
    """run_shell passes cwd parameter to subprocess."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("zsiga.transport.subprocess.run", return_value=mock_result) as mock_run:
        lt = LocalTransport()
        lt.run_shell("ls", cwd="/tmp")

    _, kwargs = mock_run.call_args
    assert kwargs.get("cwd") == "/tmp"


def test_run_shell_passes_timeout_and_stdin_data():
    """run_shell passes timeout and stdin_data to subprocess."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("zsiga.transport.subprocess.run", return_value=mock_result) as mock_run:
        lt = LocalTransport()
        lt.run_shell("cat", timeout=30, stdin_data="hello")

    _, kwargs = mock_run.call_args
    assert kwargs.get("timeout") == 30
    assert kwargs.get("input") == "hello"


def test_local_transport_close_is_noop():
    """LocalTransport.close is a no-op (inherited from Transport)."""
    lt = LocalTransport()
    # Should not raise and returns None
    result = lt.close()
    assert result is None
