"""Spec tests for SSHTransport.

Covers specs: ssh-transport.md
"""
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from zsiga.transport import SSHTransport


class TestSSHTransportInit:
    """SSHTransport constructor stores parameters."""

    def test_stores_all_constructor_params(self):
        """Scenario: SSHTransport stores all constructor params."""
        t = SSHTransport(host="myhost", user="alice", port=2222,
                         key_path="~/.ssh/id_rsa")
        assert t.host == "myhost"
        assert t.user == "alice"
        assert t.port == 2222
        assert t.key_path == str(Path("~/.ssh/id_rsa").expanduser())
        assert t._control_path is None

    def test_defaults_for_optional_params(self):
        """Scenario: SSHTransport defaults for optional params."""
        t = SSHTransport(host="myhost")
        assert t.user is None
        assert t.port == 22
        assert t.key_path is None
        assert t._control_path is None


class TestSSHTransportTarget:
    """SSHTransport._target builds user@host string."""

    def test_target_with_user(self):
        """Scenario: _target with user returns user@host."""
        t = SSHTransport(host="server", user="bob")
        assert t._target() == "bob@server"

    def test_target_without_user(self):
        """Scenario: _target without user returns host only."""
        t = SSHTransport(host="server")
        assert t._target() == "server"


class TestSSHTransportBaseArgs:
    """SSHTransport._base_args assembles SSH arguments."""

    def _make(self, **kwargs):
        t = SSHTransport(**kwargs)
        t._control_path = "/tmp/ctrl"
        return t

    def test_includes_port_when_non_default(self):
        """Scenario: _base_args includes port when non-default."""
        t = self._make(host="h", port=2222)
        args = t._base_args()
        assert "-p" in args
        idx = args.index("-p")
        assert args[idx + 1] == "2222"

    def test_omits_port_when_default_22(self):
        """Scenario: _base_args omits port when default 22."""
        t = self._make(host="h", port=22)
        args = t._base_args()
        assert "-p" not in args

    def test_includes_key_path_when_set(self):
        """Scenario: _base_args includes key_path when set."""
        t = self._make(host="h", key_path="/home/user/.ssh/key")
        args = t._base_args()
        assert "-i" in args
        idx = args.index("-i")
        assert args[idx + 1] == "/home/user/.ssh/key"


class TestSSHTransportEnsureControl:
    """SSHTransport._ensure_control is idempotent."""

    def test_skips_when_control_path_already_set(self):
        """Scenario: _ensure_control skips when control_path already set."""
        t = SSHTransport(host="h")
        t._control_path = "/tmp/existing"

        with patch("zsiga.transport.subprocess.run") as mock_run:
            t._ensure_control()
            mock_run.assert_not_called()

        assert t._control_path == "/tmp/existing"


class TestSSHTransportRunShell:
    """SSHTransport.run_shell handles timeouts and errors."""

    def _make(self):
        t = SSHTransport(host="h")
        t._control_path = "/tmp/ctrl"
        return t

    @patch("zsiga.transport.subprocess.run")
    def test_returns_timeout_dict_on_timeout_expired(self, mock_run):
        """Scenario: SSHTransport.run_shell returns timeout dict on TimeoutExpired."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=1)
        t = self._make()
        result = t.run_shell("sleep 999", timeout=1)
        assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}

    @patch("zsiga.transport.subprocess.run")
    def test_returns_error_dict_on_generic_exception(self, mock_run):
        """Scenario: SSHTransport.run_shell returns error dict on generic Exception."""
        mock_run.side_effect = OSError("Network unreachable")
        t = self._make()
        result = t.run_shell("ls")
        assert result == {"exit_code": -1, "stdout": "", "stderr": "Network unreachable"}

    @patch("zsiga.transport.subprocess.run")
    def test_prefixes_cwd_to_command(self, mock_run):
        """Scenario: SSHTransport.run_shell prefixes cwd to command."""
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = ""
        proc.stderr = ""
        mock_run.return_value = proc

        t = self._make()
        t.run_shell("ls", cwd="/var/log")

        call_args = mock_run.call_args
        ssh_args = call_args[0][0]  # first positional argument = args list
        # The last two args are target and command
        assert "cd '/var/log' && ls" in ssh_args


class TestSSHTransportClose:
    """SSHTransport.close tears down control master."""

    @patch("zsiga.transport.subprocess.run")
    def test_sends_ssh_exit_and_resets_control_path(self, mock_run):
        """Scenario: SSHTransport.close sends ssh -O exit and resets control_path."""
        t = SSHTransport(host="h")
        t._control_path = "/tmp/ctrl"

        t.close()

        call_args = mock_run.call_args[0][0]
        assert "-O" in call_args
        assert "exit" in call_args
        assert t._control_path is None

    def test_noop_when_no_control_path(self):
        """Scenario: SSHTransport.close is no-op when no control path."""
        t = SSHTransport(host="h")
        assert t._control_path is None

        with patch("zsiga.transport.subprocess.run") as mock_run:
            t.close()
            mock_run.assert_not_called()
