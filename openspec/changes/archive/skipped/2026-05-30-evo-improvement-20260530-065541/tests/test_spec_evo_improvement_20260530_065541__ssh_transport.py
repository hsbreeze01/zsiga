"""
Spec tests for SSHTransport.
Change: evo-improvement-20260530-065541
Spec: ssh-transport
"""
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from zsiga.transport import SSHTransport


class TestSSHTransportInit:

    def test_init_stores_host_and_defaults(self):
        """Scenario: SSHTransport.__init__ stores host and defaults"""
        t = SSHTransport(host="example.com")
        assert t.host == "example.com"
        assert t.user is None
        assert t.port == 22
        assert t.key_path is None

    def test_init_expands_key_path(self):
        """Scenario: SSHTransport.__init__ expands key_path"""
        t = SSHTransport(host="example.com", key_path="~/id_rsa")
        expected = str(Path("~/id_rsa").expanduser())
        assert t.key_path == expected
        assert t.key_path != "~/id_rsa"


class TestSSHTransportTarget:

    def test_target_with_user_returns_user_at_host(self):
        """Scenario: _target with user returns user@host"""
        t = SSHTransport(host="myhost", user="admin")
        assert t._target() == "admin@myhost"

    def test_target_without_user_returns_host_only(self):
        """Scenario: _target without user returns host only"""
        t = SSHTransport(host="myhost")
        assert t._target() == "myhost"


class TestSSHTransportBaseArgs:

    def test_base_args_default_port_no_key(self):
        """Scenario: _base_args with default port and no key_path"""
        t = SSHTransport(host="h")
        args = t._base_args()
        assert "ssh" in args
        assert "StrictHostKeyChecking=no" in args
        assert "-p" not in args
        assert "-i" not in args

    def test_base_args_custom_port_and_key(self):
        """Scenario: _base_args with custom port and key_path"""
        t = SSHTransport(host="h", port=2222, key_path="/key")
        args = t._base_args()
        assert "-p" in args
        assert "2222" in args
        assert "-i" in args
        assert "/key" in args


class TestSSHTransportEnsureControl:

    @patch("zsiga.transport.subprocess.run")
    @patch("zsiga.transport.tempfile.mktemp", return_value="/tmp/zsiga_ssh_mock")
    def test_ensure_control_calls_subprocess_on_first_invocation(self, mock_mktemp, mock_run):
        """Scenario: _ensure_control calls subprocess on first invocation"""
        t = SSHTransport(host="h", user="u")
        t._ensure_control()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "ControlMaster=auto" in call_args
        assert "ControlPersist=600" in call_args

    @patch("zsiga.transport.subprocess.run")
    @patch("zsiga.transport.tempfile.mktemp", return_value="/tmp/zsiga_ssh_mock")
    def test_ensure_control_is_idempotent(self, mock_mktemp, mock_run):
        """Scenario: _ensure_control is idempotent"""
        t = SSHTransport(host="h", user="u")
        t._ensure_control()
        t._ensure_control()

        assert mock_run.call_count == 1


class TestSSHTransportRunShell:

    @patch("zsiga.transport.subprocess.run")
    @patch("zsiga.transport.tempfile.mktemp", return_value="/tmp/zsiga_ssh_mock")
    def test_run_shell_prepends_cwd_to_remote_command(self, mock_mktemp, mock_run):
        """Scenario: run_shell prepends cwd to remote command"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        t = SSHTransport(host="h")
        t._control_path = "/tmp/existing"
        t.run_shell("ls", cwd="/tmp")

        # The last subprocess.run call (the command execution, not control setup)
        last_call_args = mock_run.call_args[0][0]
        # Join args to check the remote command string
        assert "cd '/tmp' && ls" in last_call_args

    @patch("zsiga.transport.subprocess.run")
    @patch("zsiga.transport.tempfile.mktemp", return_value="/tmp/zsiga_ssh_mock")
    def test_run_shell_handles_timeout_gracefully(self, mock_mktemp, mock_run):
        """Scenario: run_shell handles timeout gracefully"""
        # First call: _ensure_control succeeds
        # Second call: actual command times out
        mock_run.side_effect = [
            MagicMock(),  # _ensure_control subprocess.run
            subprocess.TimeoutExpired(cmd="ssh", timeout=5),
        ]

        t = SSHTransport(host="h")
        result = t.run_shell("sleep 999", timeout=5)

        assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}


class TestSSHTransportClose:

    @patch("zsiga.transport.subprocess.run")
    def test_close_sends_exit_signal_to_control_master(self, mock_run):
        """Scenario: close sends exit signal to control master"""
        t = SSHTransport(host="h", user="u")
        t._control_path = "/tmp/zsiga_ctrl"

        t.close()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "-O" in call_args
        assert "exit" in call_args
        assert t._control_path is None

    @patch("zsiga.transport.subprocess.run")
    def test_close_is_noop_without_control_path(self, mock_run):
        """Scenario: close is no-op without control path"""
        t = SSHTransport(host="h")
        assert t._control_path is None

        t.close()

        mock_run.assert_not_called()
