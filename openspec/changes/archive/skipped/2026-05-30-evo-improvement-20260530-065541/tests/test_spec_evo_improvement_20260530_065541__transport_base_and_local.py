"""
Spec tests for transport base class and LocalTransport.
Change: evo-improvement-20260530-065541
Spec: transport-base-and-local
"""
from unittest.mock import MagicMock, patch

from zsiga.transport import LocalTransport, Transport


class TestTransportBaseClass:

    def test_transport_run_shell_raises_not_implemented_error(self):
        """Scenario: Transport.run_shell raises NotImplementedError"""
        t = Transport()
        import pytest
        with pytest.raises(NotImplementedError):
            t.run_shell("echo hi")

    def test_transport_close_is_noop(self):
        """Scenario: Transport.close is a no-op"""
        t = Transport()
        result = t.close()
        assert result is None


class TestLocalTransportRunShell:

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_returns_subprocess_output_on_success(self, mock_run):
        """Scenario: LocalTransport.run_shell returns subprocess output on success"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        t = LocalTransport()
        result = t.run_shell("echo hello")

        assert result == {"exit_code": 0, "stdout": "hello\n", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_returns_nonzero_exit_code_on_failure(self, mock_run):
        """Scenario: LocalTransport.run_shell returns non-zero exit_code on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error msg"
        mock_run.return_value = mock_result

        t = LocalTransport()
        result = t.run_shell("false")

        assert result == {"exit_code": 1, "stdout": "", "stderr": "error msg"}
