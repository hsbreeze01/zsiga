"""Tests for zsiga/transport.py — Transport, LocalTransport, SSHTransport, create_transport."""
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from zsiga.transport import (
    LocalTransport,
    SSHTransport,
    Transport,
    create_transport,
)


# ── Transport base class ──────────────────────────────────────────────


class TestTransportBaseClass:
    def test_run_shell_raises_not_implemented_error(self):
        """Transport.run_shell() SHALL raise NotImplementedError."""
        t = Transport()
        with pytest.raises(NotImplementedError):
            t.run_shell("echo hi")

    def test_close_is_noop(self):
        """Transport.close() SHALL return None without raising."""
        t = Transport()
        result = t.close()
        assert result is None


# ── LocalTransport ────────────────────────────────────────────────────


class TestLocalTransport:
    def _mock_subprocess_run(self, returncode=0, stdout="hello\n", stderr=""):
        """Create a mock subprocess.run that returns a CompletedProcess-like object."""
        mock_cp = MagicMock()
        mock_cp.returncode = returncode
        mock_cp.stdout = stdout
        mock_cp.stderr = stderr
        return mock_cp

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_returns_subprocess_result(self, mock_run):
        """LocalTransport.run_shell() SHALL return dict with exit_code, stdout, stderr."""
        mock_run.return_value = self._mock_subprocess_run(
            returncode=0, stdout="hello\n", stderr=""
        )
        lt = LocalTransport()
        result = lt.run_shell("echo hello")
        assert result == {"exit_code": 0, "stdout": "hello\n", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_forwards_cwd(self, mock_run):
        """LocalTransport.run_shell() SHALL pass cwd to subprocess.run."""
        mock_run.return_value = self._mock_subprocess_run()
        lt = LocalTransport()
        lt.run_shell("ls", cwd="/tmp")
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == "/tmp"

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_forwards_timeout(self, mock_run):
        """LocalTransport.run_shell() SHALL pass timeout to subprocess.run."""
        mock_run.return_value = self._mock_subprocess_run()
        lt = LocalTransport()
        lt.run_shell("ls", timeout=30)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 30

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_forwards_stdin_data(self, mock_run):
        """LocalTransport.run_shell() SHALL pass stdin_data as input to subprocess.run."""
        mock_run.return_value = self._mock_subprocess_run()
        lt = LocalTransport()
        lt.run_shell("cat", stdin_data="hello")
        _, kwargs = mock_run.call_args
        assert kwargs["input"] == "hello"

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_uses_shell_and_captures(self, mock_run):
        """LocalTransport.run_shell() SHALL call subprocess.run with shell=True, capture_output, text=True."""
        mock_run.return_value = self._mock_subprocess_run()
        lt = LocalTransport()
        lt.run_shell("echo hi")
        _, kwargs = mock_run.call_args
        assert kwargs["shell"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True


# ── SSHTransport ──────────────────────────────────────────────────────


class TestSSHTransportInit:
    def test_stores_all_parameters(self):
        """SSHTransport.__init__ SHALL store host, user, port, key_path."""
        t = SSHTransport(host="myhost", user="ubuntu", port=2222, key_path="~/id_rsa")
        assert t.host == "myhost"
        assert t.user == "ubuntu"
        assert t.port == 2222
        assert t.key_path == str(Path("~/id_rsa").expanduser())
        assert t._control_path is None

    def test_defaults_user_none_port_22(self):
        """SSHTransport.__init__ SHALL default user=None, port=22, key_path=None."""
        t = SSHTransport(host="myhost")
        assert t.user is None
        assert t.port == 22
        assert t.key_path is None
        assert t._control_path is None


class TestSSHTransportTarget:
    def test_target_with_user(self):
        """_target() SHALL return 'user@host' when user is set."""
        t = SSHTransport(host="server", user="admin")
        assert t._target() == "admin@server"

    def test_target_without_user(self):
        """_target() SHALL return just host when user is None."""
        t = SSHTransport(host="server")
        assert t._target() == "server"


class TestSSHTransportBaseArgs:
    def test_base_args_default_port_no_key(self):
        """_base_args() SHALL include StrictHostKeyChecking=no and ControlPath, no -p/-i."""
        t = SSHTransport(host="h")
        t._control_path = "/tmp/sock"
        args = t._base_args()
        assert "StrictHostKeyChecking=no" in args
        assert "ControlPath=/tmp/sock" in args
        assert "-p" not in args
        assert "-i" not in args

    def test_base_args_custom_port_and_key(self):
        """_base_args() SHALL include -p and -i when port!=22 and key_path is set."""
        t = SSHTransport(host="h", port=2222, key_path="/home/u/.ssh/id_rsa")
        t._control_path = "/tmp/sock"
        args = t._base_args()
        assert "-p" in args
        assert "2222" in args
        assert "-i" in args
        assert "/home/u/.ssh/id_rsa" in args


class TestSSHTransportEnsureControl:
    @patch("zsiga.transport.subprocess.run")
    @patch("zsiga.transport.tempfile.mktemp", return_value="/tmp/zsiga_mock_sock")
    def test_creates_control_path_on_first_call(self, mock_mktemp, mock_run):
        """_ensure_control() SHALL create control path and call subprocess.run."""
        t = SSHTransport(host="h", user="u")
        t._ensure_control()
        assert t._control_path == "/tmp/zsiga_mock_sock"
        mock_run.assert_called_once()
        called_args = mock_run.call_args[0][0]
        assert "ControlMaster=auto" in called_args

    def test_idempotent_when_control_path_exists(self):
        """_ensure_control() SHALL NOT call subprocess.run if _control_path is already set."""
        t = SSHTransport(host="h")
        t._control_path = "/tmp/existing"
        with patch("zsiga.transport.subprocess.run") as mock_run:
            t._ensure_control()
            mock_run.assert_not_called()


class TestSSHTransportRunShell:
    def _make_transport(self):
        t = SSHTransport(host="h", user="u")
        t._control_path = "/tmp/sock"  # skip _ensure_control
        return t

    @patch("zsiga.transport.subprocess.run")
    def test_prepends_cwd_to_command(self, mock_run):
        """run_shell() SHALL prepend 'cd {cwd} &&' when cwd is given."""
        mock_cp = MagicMock(returncode=0, stdout="", stderr="")
        mock_run.return_value = mock_cp
        t = self._make_transport()
        t.run_shell("ls", cwd="/tmp")
        called_args = mock_run.call_args[0][0]
        assert called_args[-1] == "cd '/tmp' && ls"

    @patch("zsiga.transport.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=1))
    def test_handles_timeout(self, mock_run):
        """run_shell() SHALL return exit_code=-1 and timeout message on TimeoutExpired."""
        t = self._make_transport()
        result = t.run_shell("sleep 999", timeout=1)
        assert result["exit_code"] == -1
        assert result["stdout"] == ""
        assert "Timeout after 1s" in result["stderr"]

    @patch("zsiga.transport.subprocess.run", side_effect=OSError("network error"))
    def test_handles_generic_exception(self, mock_run):
        """run_shell() SHALL return exit_code=-1 and error message on generic exception."""
        t = self._make_transport()
        result = t.run_shell("ls")
        assert result["exit_code"] == -1
        assert result["stdout"] == ""
        assert "network error" in result["stderr"]


class TestSSHTransportClose:
    @patch("zsiga.transport.subprocess.run")
    def test_sends_exit_signal(self, mock_run):
        """close() SHALL call ssh -O exit and reset _control_path to None."""
        t = SSHTransport(host="h", user="u")
        t._control_path = "/tmp/sock"
        t.close()
        called_args = mock_run.call_args[0][0]
        assert "-O" in called_args
        assert "exit" in called_args
        assert t._control_path is None

    def test_noop_without_control_path(self):
        """close() SHALL NOT call subprocess.run when _control_path is None."""
        t = SSHTransport(host="h")
        with patch("zsiga.transport.subprocess.run") as mock_run:
            t.close()
            mock_run.assert_not_called()


# ── create_transport factory ──────────────────────────────────────────


class TestCreateTransport:
    def test_returns_local_when_ssh_none(self):
        """create_transport() SHALL return LocalTransport when ssh is None."""
        cfg = SimpleNamespace(ssh=None)
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_local_when_no_ssh_attribute(self):
        """create_transport() SHALL return LocalTransport when ssh attribute is missing."""
        cfg = SimpleNamespace()
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_ssh_when_ssh_config_present(self):
        """create_transport() SHALL return SSHTransport when ssh config is present."""
        ssh_cfg = SimpleNamespace(host="myhost", user="ubuntu", port=2222, key_path="/key")
        cfg = SimpleNamespace(ssh=ssh_cfg)
        result = create_transport(cfg)
        assert isinstance(result, SSHTransport)
        assert result.host == "myhost"
        assert result.user == "ubuntu"
        assert result.port == 2222
        assert result.key_path == "/key"
