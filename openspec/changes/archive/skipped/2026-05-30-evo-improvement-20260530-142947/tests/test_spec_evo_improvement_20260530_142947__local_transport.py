"""Spec tests for local-transport.

Change: evo-improvement-20260530-142947
Spec:   local-transport
"""

import subprocess
from unittest.mock import patch

from zsiga.transport import LocalTransport


class TestLocalTransportSpec:
    """Tests for LocalTransport subprocess delegation (spec: local-transport)."""

    @patch("zsiga.transport.subprocess.run")
    def test_returns_parsed_subprocess_result(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args="echo ok", returncode=0, stdout="ok\n", stderr=""
        )
        assert LocalTransport().run_shell("echo ok") == {
            "exit_code": 0,
            "stdout": "ok\n",
            "stderr": "",
        }

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_cwd_and_timeout(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args="ls", returncode=0, stdout="", stderr=""
        )
        LocalTransport().run_shell("ls", cwd="/tmp", timeout=30)
        mock_run.assert_called_once_with(
            "ls",
            shell=True,
            cwd="/tmp",
            capture_output=True,
            text=True,
            timeout=30,
            input=None,
        )

    @patch("zsiga.transport.subprocess.run")
    def test_forwards_stdin_data_as_input(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args="cat", returncode=0, stdout="hello", stderr=""
        )
        LocalTransport().run_shell("cat", stdin_data="hello")
        mock_run.assert_called_once_with(
            "cat",
            shell=True,
            cwd=None,
            capture_output=True,
            text=True,
            timeout=120,
            input="hello",
        )
