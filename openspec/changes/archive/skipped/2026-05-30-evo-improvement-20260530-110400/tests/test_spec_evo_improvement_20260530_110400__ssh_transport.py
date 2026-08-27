"""Tests for ssh-transport spec.

Covers SSHTransport constructor, _target, _base_args, _ensure_control,
run_shell, and close.
"""
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from zsiga.transport import SSHTransport


class TestSSHTransportInit:
    def test_stores_all_parameters(self):
        """Scenario: SSHTransport.__init__ stores all parameters"""
        t = SSHTransport(host="myhost", user="alice", port=2222, key_path="~/id_rsa")
        assert t.host == "myhost"
        assert t.user == "alice"
        assert t.port == 2222
        assert t.key_path == str(Path("~/id_rsa").expanduser())
        assert t._control_path is None


class TestSSHTransportTarget:
    def test_target_with_user(self):
        """Scenario: _target with user returns user@host"""
        t = SSHTransport(host="srv", user="bob")
        assert t._target() == "bob@srv"

    def test_target_without_user(self):
        """Scenario: _target without user returns host only"""
        t = SSHTransport(host="srv", user=None)
        assert t._target() == "srv"


class TestSSHTransportBaseArgs:
    def test_default_port_no_key(self):
        """Scenario: _base_args with default port and no key"""
        t = SSHTransport(host="srv")
        args = t._base_args()
        assert "-p" not in args
        assert "-i" not in args

    def test_custom_port_and_key(self):
        """Scenario: _base_args with custom port and key"""
        t = SSHTransport(host="srv", port=2222, key_path="/home/alice/.ssh/id_rsa")
        args = t._base_args()
        assert "-p" in args
        assert "2222" in args
        assert "-i" in args
        assert "/home/alice/.ssh/id_rsa" in args


class TestSSHTransportEnsureControl:
    @patch("zsiga.transport.subprocess.run")
    @patch("zsiga.transport.tempfile.mktemp", return_value="/tmp/zsiga_ctrl_123")
    def test_idempotent(self, mock_mktemp, mock_run):
        """Scenario: _ensure_control is idempotent"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        t = SSHTransport(host="srv", user="alice")
        t._ensure_control()
        t._ensure_control()
        # subprocess.run should only be called once (first call sets _control_path)
        assert mock_run.call_count == 1


class TestSSHTransportRunShell:
    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_cwd_prepends_cd(self, mock_ensure, mock_run):
        """Scenario: run_shell with cwd prepends cd command"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        t = SSHTransport(host="srv", user="alice")
        t.run_shell("ls", cwd="/tmp")
        # The last positional arg of subprocess.run should contain cd prefix
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        # Find the remote command (last element of the ssh args)
        assert "cd '/tmp' && ls" in ssh_cmd

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_handles_timeout_expired(self, mock_ensure, mock_run):
        """Scenario: run_shell handles TimeoutExpired"""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=5)
        t = SSHTransport(host="srv", user="alice")
        result = t.run_shell("sleep 999", timeout=5)
        assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_handles_generic_exception(self, mock_ensure, mock_run):
        """Scenario: run_shell handles generic exception"""
        mock_run.side_effect = OSError("network down")
        t = SSHTransport(host="srv", user="alice")
        result = t.run_shell("ls")
        assert result["exit_code"] == -1
        assert result["stdout"] == ""
        assert result["stderr"] == "network down"

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_no_cwd_passes_command_directly(self, mock_ensure, mock_run):
        """Scenario: run_shell without cwd passes command directly"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        t = SSHTransport(host="srv", user="alice")
        t.run_shell("ls")
        call_args = mock_run.call_args
        ssh_cmd = call_args[0][0]
        # Last element should be exactly "ls"
        assert ssh_cmd[-1] == "ls"


class TestSSHTransportClose:
    @patch("zsiga.transport.subprocess.run")
    def test_close_sends_exit_command(self, mock_run):
        """Scenario: close with active control path sends exit command"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        t = SSHTransport(host="srv", user="alice")
        t._control_path = "/tmp/zsiga_ctrl"
        t.close()
        call_args = mock_run.call_args[0][0]
        assert "-O" in call_args
        assert "exit" in call_args
        assert t._control_path is None

    def test_close_with_no_control_path_is_noop(self):
        """Scenario: close with no control path is a no-op"""
        t = SSHTransport(host="srv", user="alice")
        t._control_path = None
        # Should not call subprocess.run at all — we don't patch it,
        # so if it does call, it would fail.
        t.close()
        # If we reach here, no subprocess.run was called
        assert t._control_path is None
