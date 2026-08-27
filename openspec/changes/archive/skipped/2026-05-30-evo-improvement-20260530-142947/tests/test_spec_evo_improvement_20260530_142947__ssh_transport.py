"""Spec tests for ssh-transport.

Change: evo-improvement-20260530-142947
Spec:   ssh-transport
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

from zsiga.transport import SSHTransport


class TestSSHTransportInitSpec:
    def test_stores_params_and_expands_key_path(self):
        t = SSHTransport(host="myhost", user="alice", port=2222, key_path="~/id_rsa")
        assert t.host == "myhost"
        assert t.user == "alice"
        assert t.port == 2222
        assert t.key_path == str(Path("~/id_rsa").expanduser())
        assert t._control_path is None


class TestSSHTransportTargetSpec:
    def test_with_user(self):
        t = SSHTransport(host="myhost", user="alice")
        assert t._target() == "alice@myhost"

    def test_without_user(self):
        t = SSHTransport(host="myhost", user=None)
        assert t._target() == "myhost"


class TestSSHTransportBaseArgsSpec:
    def test_includes_port_and_key_path(self):
        t = SSHTransport(host="h", port=2222, key_path="/home/u/.ssh/id")
        t._control_path = "/tmp/ctrl"
        args = t._base_args()
        assert "StrictHostKeyChecking=no" in args
        assert "-p" in args
        assert "2222" in args
        assert "-i" in args
        assert "/home/u/.ssh/id" in args

    def test_omits_port_when_22(self):
        t = SSHTransport(host="h", port=22)
        args = t._base_args()
        assert "-p" not in args


class TestSSHTransportRunShellSpec:
    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_prepends_cwd_to_command(self, mock_ensure, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="out", stderr=""
        )
        t = SSHTransport(host="h", user="u")
        t.run_shell("ls", cwd="/tmp")
        last_arg = mock_run.call_args[0][0][-1]
        assert last_arg == "cd '/tmp' && ls"

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_handles_timeout_expired(self, mock_ensure, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=5)
        t = SSHTransport(host="h", user="u")
        result = t.run_shell("sleep 999", timeout=5)
        assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_handles_generic_exception(self, mock_ensure, mock_run):
        mock_run.side_effect = OSError("network down")
        t = SSHTransport(host="h", user="u")
        result = t.run_shell("ls")
        assert result == {"exit_code": -1, "stdout": "", "stderr": "network down"}


class TestSSHTransportCloseSpec:
    @patch("zsiga.transport.subprocess.run")
    def test_sends_exit_via_control_master(self, mock_run):
        t = SSHTransport(host="h", user="u")
        t._control_path = "/tmp/ctrl"
        t.close()
        run_args = mock_run.call_args[0][0]
        assert "-O" in run_args
        assert "exit" in run_args
        assert t._control_path is None

    @patch("zsiga.transport.subprocess.run")
    def test_noop_when_no_control_path(self, mock_run):
        t = SSHTransport(host="h", user="u")
        t._control_path = None
        result = t.close()
        mock_run.assert_not_called()
        assert result is None


class TestSSHTransportEnsureControlSpec:
    @patch("zsiga.transport.subprocess.run")
    def test_establishes_control_master(self, mock_run):
        t = SSHTransport(host="h", user="u")
        assert t._control_path is None
        t._ensure_control()
        assert t._control_path is not None
        run_args = mock_run.call_args[0][0]
        assert "ControlMaster=auto" in run_args
