"""Spec tests for transport abstract base, local, SSH, and factory.

Change: evo-improvement-20260530-142947
Specs:  transport-abstract-base, local-transport, ssh-transport, create-transport-factory
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zsiga.transport import (
    LocalTransport,
    SSHTransport,
    Transport,
    create_transport,
)


# ---------------------------------------------------------------------------
# transport-abstract-base scenarios
# ---------------------------------------------------------------------------


class TestTransportAbstractBase:
    """Tests for Transport base class interface contract."""

    def test_run_shell_raises_not_implemented_error(self):
        """Scenario: Transport.run_shell raises NotImplementedError."""
        t = Transport()
        with pytest.raises(NotImplementedError):
            t.run_shell("echo hi")

    def test_close_returns_none(self):
        """Scenario: Transport.close returns None."""
        t = Transport()
        assert t.close() is None


# ---------------------------------------------------------------------------
# local-transport scenarios
# ---------------------------------------------------------------------------


class TestLocalTransport:
    """Tests for LocalTransport subprocess delegation."""

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_returns_parsed_subprocess_result(self, mock_run):
        """Scenario: LocalTransport.run_shell returns parsed subprocess result."""
        mock_run.return_value = subprocess.CompletedProcess(
            args="echo ok", returncode=0, stdout="ok\n", stderr=""
        )
        t = LocalTransport()
        result = t.run_shell("echo ok")
        assert result == {"exit_code": 0, "stdout": "ok\n", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_run_shell_forwards_cwd_and_timeout(self, mock_run):
        """Scenario: LocalTransport.run_shell forwards cwd and timeout."""
        mock_run.return_value = subprocess.CompletedProcess(
            args="ls", returncode=0, stdout="", stderr=""
        )
        t = LocalTransport()
        t.run_shell("ls", cwd="/tmp", timeout=30)
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
    def test_run_shell_forwards_stdin_data_as_input(self, mock_run):
        """Scenario: LocalTransport.run_shell forwards stdin_data as input."""
        mock_run.return_value = subprocess.CompletedProcess(
            args="cat", returncode=0, stdout="hello", stderr=""
        )
        t = LocalTransport()
        t.run_shell("cat", stdin_data="hello")
        mock_run.assert_called_once_with(
            "cat",
            shell=True,
            cwd=None,
            capture_output=True,
            text=True,
            timeout=120,
            input="hello",
        )


# ---------------------------------------------------------------------------
# ssh-transport scenarios
# ---------------------------------------------------------------------------


class TestSSHTransportInit:
    """Tests for SSHTransport __init__ and parameter storage."""

    def test_stores_params_and_expands_key_path(self):
        """Scenario: SSHTransport stores init params and expands key_path."""
        t = SSHTransport(host="myhost", user="alice", port=2222, key_path="~/id_rsa")
        assert t.host == "myhost"
        assert t.user == "alice"
        assert t.port == 2222
        assert t.key_path == str(Path("~/id_rsa").expanduser())
        assert t._control_path is None


class TestSSHTransportTarget:
    """Tests for SSHTransport._target."""

    def test_target_with_user(self):
        """Scenario: _target returns user@host when user provided."""
        t = SSHTransport(host="myhost", user="alice")
        assert t._target() == "alice@myhost"

    def test_target_without_user(self):
        """Scenario: _target returns host only when user is None."""
        t = SSHTransport(host="myhost", user=None)
        assert t._target() == "myhost"


class TestSSHTransportBaseArgs:
    """Tests for SSHTransport._base_args."""

    def test_base_args_includes_port_and_key_path(self):
        """Scenario: _base_args includes strict host checking disabled and key_path."""
        t = SSHTransport(host="h", port=2222, key_path="/home/u/.ssh/id")
        t._control_path = "/tmp/ctrl"
        args = t._base_args()
        assert "StrictHostKeyChecking=no" in args
        assert "-p" in args
        assert "2222" in args
        assert "-i" in args
        assert "/home/u/.ssh/id" in args

    def test_base_args_omits_port_when_22(self):
        """Scenario: _base_args omits port when port is 22."""
        t = SSHTransport(host="h", port=22)
        args = t._base_args()
        assert "-p" not in args


class TestSSHTransportRunShell:
    """Tests for SSHTransport.run_shell."""

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_run_shell_prepends_cwd_to_command(self, mock_ensure, mock_run):
        """Scenario: run_shell prepends cwd to command."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="file.txt", stderr=""
        )
        t = SSHTransport(host="h", user="u")
        t.run_shell("ls", cwd="/tmp")
        # Last positional arg to subprocess.run is the remote command
        last_arg = mock_run.call_args[0][0][-1]
        assert last_arg == "cd '/tmp' && ls"

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_run_shell_handles_timeout_expired(self, mock_ensure, mock_run):
        """Scenario: run_shell handles TimeoutExpired."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=5)
        t = SSHTransport(host="h", user="u")
        result = t.run_shell("sleep 999", timeout=5)
        assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}

    @patch("zsiga.transport.subprocess.run")
    @patch.object(SSHTransport, "_ensure_control")
    def test_run_shell_handles_generic_os_error(self, mock_ensure, mock_run):
        """Scenario: run_shell handles generic OSError."""
        mock_run.side_effect = OSError("network down")
        t = SSHTransport(host="h", user="u")
        result = t.run_shell("ls")
        assert result == {"exit_code": -1, "stdout": "", "stderr": "network down"}


class TestSSHTransportClose:
    """Tests for SSHTransport.close."""

    @patch("zsiga.transport.subprocess.run")
    def test_close_sends_exit_via_control_master(self, mock_run):
        """Scenario: close sends exit via control master."""
        t = SSHTransport(host="h", user="u")
        t._control_path = "/tmp/ctrl"
        t.close()
        run_args = mock_run.call_args[0][0]
        assert "-O" in run_args
        assert "exit" in run_args
        assert t._control_path is None

    @patch("zsiga.transport.subprocess.run")
    def test_close_is_noop_when_no_control_path(self, mock_run):
        """Scenario: close is no-op when no control path."""
        t = SSHTransport(host="h", user="u")
        t._control_path = None
        result = t.close()
        mock_run.assert_not_called()
        assert result is None


class TestSSHTransportEnsureControl:
    """Tests for SSHTransport._ensure_control."""

    @patch("zsiga.transport.subprocess.run")
    def test_ensure_control_establishes_control_master(self, mock_run):
        """Scenario: _ensure_control establishes control master."""
        t = SSHTransport(host="h", user="u")
        assert t._control_path is None
        t._ensure_control()
        assert t._control_path is not None
        run_args = mock_run.call_args[0][0]
        assert "ControlMaster=auto" in run_args


# ---------------------------------------------------------------------------
# create-transport-factory scenarios
# ---------------------------------------------------------------------------


class TestCreateTransportFactory:
    """Tests for create_transport factory function."""

    def test_returns_ssh_transport_for_ssh_target(self):
        """Scenario: create_transport returns SSHTransport for ssh target."""
        cfg = MagicMock()
        cfg.ssh = MagicMock()
        cfg.ssh.host = "h"
        cfg.ssh.user = "u"
        cfg.ssh.port = 22
        cfg.ssh.key_path = "/key"
        result = create_transport(cfg)
        assert isinstance(result, SSHTransport)
        assert result.host == "h"
        assert result.user == "u"
        assert result.port == 22
        assert result.key_path == "/key"

    def test_returns_local_transport_when_ssh_is_none(self):
        """Scenario: create_transport returns LocalTransport when ssh is None."""
        cfg = MagicMock()
        cfg.ssh = None
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_local_transport_when_ssh_is_falsy(self):
        """Scenario: create_transport returns LocalTransport when ssh is falsy."""
        cfg = MagicMock()
        cfg.ssh = False
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)
