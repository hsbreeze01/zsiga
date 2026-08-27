"""Tests for zsiga/transport.py — SSHTransport spec tests."""
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from zsiga.transport import SSHTransport


class TestSSHTransportInit:
    def test_stores_all_params(self):
        t = SSHTransport(host="myhost", user="ubuntu", port=2222, key_path="~/id_rsa")
        assert t.host == "myhost"
        assert t.user == "ubuntu"
        assert t.port == 2222
        assert t.key_path == str(Path("~/id_rsa").expanduser())
        assert t._control_path is None

    def test_defaults(self):
        t = SSHTransport(host="myhost")
        assert t.user is None
        assert t.port == 22
        assert t.key_path is None
        assert t._control_path is None


class TestSSHTransportTarget:
    def test_with_user(self):
        t = SSHTransport(host="server", user="admin")
        assert t._target() == "admin@server"

    def test_without_user(self):
        t = SSHTransport(host="server")
        assert t._target() == "server"


class TestSSHTransportBaseArgs:
    def test_default_port_no_key(self):
        t = SSHTransport(host="h")
        t._control_path = "/tmp/sock"
        args = t._base_args()
        assert "StrictHostKeyChecking=no" in args
        assert "ControlPath=/tmp/sock" in args
        assert "-p" not in args
        assert "-i" not in args

    def test_custom_port_and_key(self):
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
    def test_creates_control_path(self, mock_mktemp, mock_run):
        t = SSHTransport(host="h", user="u")
        t._ensure_control()
        assert t._control_path == "/tmp/zsiga_mock_sock"
        called_args = mock_run.call_args[0][0]
        assert "ControlMaster=auto" in called_args

    def test_idempotent(self):
        t = SSHTransport(host="h")
        t._control_path = "/tmp/existing"
        with patch("zsiga.transport.subprocess.run") as mock_run:
            t._ensure_control()
            mock_run.assert_not_called()


class TestSSHTransportRunShell:
    def _make(self):
        t = SSHTransport(host="h", user="u")
        t._control_path = "/tmp/sock"
        return t

    @patch("zsiga.transport.subprocess.run")
    def test_prepends_cwd(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        t = self._make()
        t.run_shell("ls", cwd="/tmp")
        assert mock_run.call_args[0][0][-1] == "cd '/tmp' && ls"

    @patch("zsiga.transport.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=1))
    def test_timeout(self, mock_run):
        t = self._make()
        r = t.run_shell("sleep 999", timeout=1)
        assert r["exit_code"] == -1
        assert r["stdout"] == ""
        assert "Timeout after 1s" in r["stderr"]

    @patch("zsiga.transport.subprocess.run", side_effect=OSError("network error"))
    def test_generic_exception(self, mock_run):
        t = self._make()
        r = t.run_shell("ls")
        assert r["exit_code"] == -1
        assert r["stdout"] == ""
        assert "network error" in r["stderr"]


class TestSSHTransportClose:
    @patch("zsiga.transport.subprocess.run")
    def test_sends_exit_signal(self, mock_run):
        t = SSHTransport(host="h", user="u")
        t._control_path = "/tmp/sock"
        t.close()
        called_args = mock_run.call_args[0][0]
        assert "-O" in called_args
        assert "exit" in called_args
        assert t._control_path is None

    def test_noop_without_control_path(self):
        t = SSHTransport(host="h")
        with patch("zsiga.transport.subprocess.run") as mock_run:
            t.close()
            mock_run.assert_not_called()
