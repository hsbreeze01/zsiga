"""Tests for spec: transport-base-and-local.md
Change: evo-improvement-20260530-054103
"""

from unittest.mock import MagicMock, patch

from zsiga.transport import LocalTransport, Transport


class TestTransportBase:
    """Transport base class scenarios."""

    def test_run_shell_raises_not_implemented_error(self):
        """Scenario: calling run_shell on Transport base raises NotImplementedError."""
        t = Transport()
        raised = False
        try:
            t.run_shell("echo hello")
        except NotImplementedError:
            raised = True
        assert raised, "Transport.run_shell must raise NotImplementedError"

    def test_close_returns_none(self):
        """Scenario: calling close on Transport base does not raise."""
        t = Transport()
        result = t.close()
        assert result is None


class TestLocalTransport:
    """LocalTransport scenarios."""

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_returns_subprocess_result_dict(self, mock_run):
        """Scenario: LocalTransport.run_shell returns subprocess result dict."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "ok\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        lt = LocalTransport()
        result = lt.run_shell("echo ok")

        assert result == {"exit_code": 0, "stdout": "ok\n", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_passes_cwd_and_timeout(self, mock_run):
        """Scenario: LocalTransport.run_shell passes cwd and timeout to subprocess."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        lt = LocalTransport()
        lt.run_shell("ls", cwd="/tmp", timeout=30)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs[1]["cwd"] == "/tmp"
        assert call_kwargs[1]["timeout"] == 30

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_passes_stdin_data_as_input(self, mock_run):
        """Scenario: LocalTransport.run_shell passes stdin_data as input."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        lt = LocalTransport()
        lt.run_shell("cat", stdin_data="hello")

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs[1]["input"] == "hello"
