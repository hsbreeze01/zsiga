"""Tests for ssh-transport.md spec scenarios.

Covers: SSHTransport.__init__, _target, _base_args, run_shell, close
"""
import subprocess
from unittest.mock import MagicMock, patch

from zsiga.transport import SSHTransport


class TestSSHTransportInit:
    """Spec: SSHTransport construction and attribute storage."""

    def test_stores_constructor_arguments_with_expanduser(self):
        """Scenario: SSHTransport stores constructor arguments."""
        t = SSHTransport(
            host="srv.example.com",
            user="deploy",
            port=2222,
            key_path="~/.ssh/id_rsa",
        )
        assert t.host == "srv.example.com"
        assert t.user == "deploy"
        assert t.port == 2222
        assert t.key_path.endswith("/.ssh/id_rsa")
        assert t._control_path is None

    def test_default_port_and_optional_fields(self):
        """Scenario: SSHTransport default port and optional fields."""
        t = SSHTransport(host="srv.example.com")
        assert t.user is None
        assert t.port == 22
        assert t.key_path is None
        assert t._control_path is None


class TestSSHTransportTarget:
    """Spec: SSHTransport._target constructs SSH target string."""

    def test_target_with_user(self):
        """Scenario: _target with user returns user@host."""
        t = SSHTransport(host="srv.example.com", user="deploy")
        assert t._target() == "deploy@srv.example.com"

    def test_target_without_user(self):
        """Scenario: _target without user returns host only."""
        t = SSHTransport(host="srv.example.com")
        assert t._target() == "srv.example.com"


class TestSSHTransportBaseArgs:
    """Spec: SSHTransport._base_args builds SSH argument list."""

    def test_includes_port_when_non_default(self):
        """Scenario: _base_args includes port when non-default."""
        t = SSHTransport(host="srv.example.com", port=2222)
        args = t._base_args()
        assert "-p" in args
        idx = args.index("-p")
        assert args[idx + 1] == "2222"

    def test_includes_identity_file_when_key_path_set(self):
        """Scenario: _base_args includes identity file when key_path set."""
        t = SSHTransport(host="srv.example.com", key_path="/home/user/.ssh/id_rsa")
        args = t._base_args()
        assert "-i" in args
        idx = args.index("-i")
        assert args[idx + 1] == "/home/user/.ssh/id_rsa"


class TestSSHTransportRunShell:
    """Spec: SSHTransport.run_shell executes remote command via SSH."""

    @patch("zsiga.transport.subprocess.run")
    def test_prefixes_cwd_into_remote_command(self, mock_run):
        """Scenario: SSHTransport.run_shell prefixes cwd into remote command."""
        t = SSHTransport(host="srv.example.com", user="deploy")
        t._ensure_control = MagicMock()
        mock_run.return_value = MagicMock(returncode=0, stdout="out", stderr="")
        t.run_shell("ls", cwd="/home/deploy")
        last_arg = mock_run.call_args[0][0][-1]
        assert last_arg == "cd '/home/deploy' && ls"

    @patch("zsiga.transport.subprocess.run")
    def test_handles_timeout(self, mock_run):
        """Scenario: SSHTransport.run_shell handles timeout."""
        t = SSHTransport(host="srv.example.com")
        t._ensure_control = MagicMock()
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=1)
        result = t.run_shell("sleep 999", timeout=1)
        assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}

    @patch("zsiga.transport.subprocess.run")
    def test_handles_generic_exception(self, mock_run):
        """Scenario: SSHTransport.run_shell handles generic exception."""
        t = SSHTransport(host="srv.example.com")
        t._ensure_control = MagicMock()
        mock_run.side_effect = OSError("network error")
        result = t.run_shell("cmd")
        assert result["exit_code"] == -1
        assert "network error" in result["stderr"]


class TestSSHTransportClose:
    """Spec: SSHTransport.close tears down control master."""

    @patch("zsiga.transport.subprocess.run")
    def test_sends_exit_to_control_master(self, mock_run):
        """Scenario: SSHTransport.close sends exit to control master."""
        t = SSHTransport(host="srv.example.com", user="deploy")
        t._control_path = "/tmp/zsiga_ssh_abc"
        t.close()
        called_args = mock_run.call_args[0][0]
        assert "-O" in called_args
        assert "exit" in called_args
        assert t._control_path is None

    def test_no_op_when_no_control_path(self):
        """Scenario: SSHTransport.close is no-op when no control path."""
        t = SSHTransport(host="srv.example.com")
        assert t._control_path is None
        with patch("zsiga.transport.subprocess.run") as mock_run:
            t.close()
        mock_run.assert_not_called()
        assert t._control_path is None
