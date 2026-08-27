"""Tests for zsiga/transport.py — LocalTransport spec tests."""
from unittest.mock import MagicMock, patch

from zsiga.transport import LocalTransport


class TestLocalTransportRunShell:
    def _mock_cp(self, returncode=0, stdout="hello\n", stderr=""):
        m = MagicMock()
        m.returncode = returncode
        m.stdout = stdout
        m.stderr = stderr
        return m

    @patch("zsiga.transport.subprocess.run")
    def test_returns_dict_with_exit_code_stdout_stderr(self, mock_run):
        mock_run.return_value = self._mock_cp(returncode=0, stdout="hello\n", stderr="")
        lt = LocalTransport()
        result = lt.run_shell("echo hello")
        assert result == {"exit_code": 0, "stdout": "hello\n", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_cwd_kwarg(self, mock_run):
        mock_run.return_value = self._mock_cp()
        lt = LocalTransport()
        lt.run_shell("ls", cwd="/tmp")
        assert mock_run.call_args[1]["cwd"] == "/tmp"

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_timeout_kwarg(self, mock_run):
        mock_run.return_value = self._mock_cp()
        lt = LocalTransport()
        lt.run_shell("ls", timeout=30)
        assert mock_run.call_args[1]["timeout"] == 30

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_stdin_data_as_input(self, mock_run):
        mock_run.return_value = self._mock_cp()
        lt = LocalTransport()
        lt.run_shell("cat", stdin_data="hello")
        assert mock_run.call_args[1]["input"] == "hello"

    @patch("zsiga.transport.subprocess.run")
    def test_uses_shell_true_capture_output_text_true(self, mock_run):
        mock_run.return_value = self._mock_cp()
        lt = LocalTransport()
        lt.run_shell("echo hi")
        kw = mock_run.call_args[1]
        assert kw["shell"] is True
        assert kw["capture_output"] is True
        assert kw["text"] is True
