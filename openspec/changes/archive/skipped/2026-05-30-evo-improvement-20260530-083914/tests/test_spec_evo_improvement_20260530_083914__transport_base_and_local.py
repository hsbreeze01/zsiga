"""Tests for zsiga/transport.py — Transport, LocalTransport, SSHTransport, create_transport."""
import subprocess
from subprocess import CompletedProcess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from zsiga.transport import LocalTransport, SSHTransport, Transport, create_transport


# ---------------------------------------------------------------------------
# Transport base class
# ---------------------------------------------------------------------------


class TestTransportBase:
    """Transport abstract base class contract."""

    def test_run_shell_raises_not_implemented(self):
        """Scenario: Transport.run_shell raises NotImplementedError."""
        t = Transport()
        with pytest.raises(NotImplementedError):
            t.run_shell("echo hi")

    def test_close_returns_none(self):
        """Scenario: Transport.close returns None."""
        t = Transport()
        assert t.close() is None


# ---------------------------------------------------------------------------
# LocalTransport
# ---------------------------------------------------------------------------


class TestLocalTransport:
    """LocalTransport.run_shell delegates to subprocess.run."""

    @patch("zsiga.transport.subprocess.run")
    def test_returns_exit_code_stdout_stderr_dict(self, mock_run):
        """Scenario: LocalTransport.run_shell returns exit_code stdout stderr dict."""
        mock_run.return_value = CompletedProcess(
            args="echo ok", returncode=0, stdout="ok\n", stderr=""
        )
        result = LocalTransport().run_shell("echo ok")
        assert result == {"exit_code": 0, "stdout": "ok\n", "stderr": ""}

    @patch("zsiga.transport.subprocess.run")
    def test_passes_cwd_to_subprocess(self, mock_run):
        """Scenario: LocalTransport.run_shell passes cwd to subprocess."""
        mock_run.return_value = CompletedProcess(
            args="ls", returncode=0, stdout="", stderr=""
        )
        LocalTransport().run_shell("ls", cwd="/tmp")
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == "/tmp"

    @patch("zsiga.transport.subprocess.run")
    def test_passes_stdin_data_as_input(self, mock_run):
        """Scenario: LocalTransport.run_shell passes stdin_data as input."""
        mock_run.return_value = CompletedProcess(
            args="cat", returncode=0, stdout="", stderr=""
        )
        LocalTransport().run_shell("cat", stdin_data="hello")
        _, kwargs = mock_run.call_args
        assert kwargs["input"] == "hello"

    @patch("zsiga.transport.subprocess.run")
    def test_passes_timeout_to_subprocess(self, mock_run):
        """Scenario: LocalTransport.run_shell passes timeout to subprocess."""
        mock_run.return_value = CompletedProcess(
            args="ls", returncode=0, stdout="", stderr=""
        )
        LocalTransport().run_shell("ls", timeout=30)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 30

    @patch("zsiga.transport.subprocess.run")
    def test_calls_subprocess_with_shell_and_capture(self, mock_run):
        """Scenario: LocalTransport.run_shell calls subprocess with shell=True and capture_output."""
        mock_run.return_value = CompletedProcess(
            args="echo", returncode=0, stdout="", stderr=""
        )
        LocalTransport().run_shell("echo")
        _, kwargs = mock_run.call_args
        assert kwargs["shell"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True

    @patch("zsiga.transport.subprocess.run")
    def test_nonzero_exit_code_propagated(self, mock_run):
        """LocalTransport propagates non-zero exit codes faithfully."""
        mock_run.return_value = CompletedProcess(
            args="false", returncode=1, stdout="", stderr="error"
        )
        result = LocalTransport().run_shell("false")
        assert result["exit_code"] == 1
        assert result["stderr"] == "error"


# ---------------------------------------------------------------------------
# SSHTransport — constructor
# ---------------------------------------------------------------------------


class TestSSHTransportInit:
    """SSHTransport constructor stores and expands parameters."""

    def test_stores_host_user_port_key_path(self):
        """Scenario: SSHTransport stores host user port key_path."""
        t = SSHTransport("myhost", user="ubuntu", port=2222, key_path="~/.ssh/id_rsa")
        assert t.host == "myhost"
        assert t.user == "ubuntu"
        assert t.port == 2222
        # key_path should be expanded
        assert "~" not in t.key_path
        assert t._control_path is None

    def test_defaults_user_none_port_22(self):
        """Scenario: SSHTransport defaults user to None and port to 22."""
        t = SSHTransport("myhost")
        assert t.user is None
        assert t.port == 22
        assert t.key_path is None
        assert t._control_path is None

    def test_key_path_none_stays_none(self):
        """key_path=None should remain None, not raise."""
        t = SSHTransport("h", key_path=None)
        assert t.key_path is None


# ---------------------------------------------------------------------------
# SSHTransport — _target
# ---------------------------------------------------------------------------


class TestSSHTransportTarget:
    """SSHTransport._target formats the SSH target string."""

    def test_returns_user_at_host_when_user_set(self):
        """Scenario: _target returns user@host when user is set."""
        t = SSHTransport("host1", user="root")
        assert t._target() == "root@host1"

    def test_returns_host_when_user_none(self):
        """Scenario: _target returns host when user is None."""
        t = SSHTransport("host1")
        assert t._target() == "host1"


# ---------------------------------------------------------------------------
# SSHTransport — _base_args
# ---------------------------------------------------------------------------


class TestSSHTransportBaseArgs:
    """SSHTransport._base_args builds the SSH argument list."""

    def _make(self, **kwargs):
        t = SSHTransport("host1", **kwargs)
        t._control_path = "/tmp/ctrl"
        return t

    def test_includes_port_flag_when_not_22(self):
        """Scenario: _base_args includes port flag when port is not 22."""
        args = self._make(port=2222)._base_args()
        assert "-p" in args
        assert "2222" in args

    def test_includes_identity_flag_when_key_path_set(self):
        """Scenario: _base_args includes identity flag when key_path is set."""
        args = self._make(key_path="/home/user/.ssh/id_rsa")._base_args()
        assert "-i" in args
        assert "/home/user/.ssh/id_rsa" in args

    def test_omits_port_flag_when_port_is_22(self):
        """Scenario: _base_args omits port flag when port is 22."""
        args = self._make(port=22)._base_args()
        assert "-p" not in args

    def test_always_includes_strict_host_key_checking_no(self):
        """_base_args always includes StrictHostKeyChecking=no."""
        args = self._make()._base_args()
        assert "StrictHostKeyChecking=no" in args


# ---------------------------------------------------------------------------
# SSHTransport — _ensure_control
# ---------------------------------------------------------------------------


class TestSSHTransportEnsureControl:
    """SSHTransport._ensure_control is idempotent."""

    @patch("zsiga.transport.subprocess.run")
    def test_calls_subprocess_once_and_sets_control_path(self, mock_run):
        """Scenario: _ensure_control calls subprocess.run once and sets control_path."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._ensure_control()
        assert mock_run.call_count == 1
        assert t._control_path is not None
        assert "zsiga_ssh_" in t._control_path

    @patch("zsiga.transport.subprocess.run")
    def test_idempotent_on_second_call(self, mock_run):
        """Scenario: _ensure_control is idempotent on second call."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._ensure_control()
        t._ensure_control()
        assert mock_run.call_count == 1


# ---------------------------------------------------------------------------
# SSHTransport — run_shell
# ---------------------------------------------------------------------------


class TestSSHTransportRunShell:
    """SSHTransport.run_shell prepends cd and handles timeout."""

    @patch("zsiga.transport.subprocess.run")
    def test_prefixes_cd_when_cwd_given(self, mock_run):
        """Scenario: run_shell prefixes cd when cwd is given."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout="out", stderr="")
        t = SSHTransport("host1")
        t._control_path = "/tmp/ctrl"
        t.run_shell("ls", cwd="/var")
        call_args = mock_run.call_args[0][0]
        assert "cd '/var' && ls" in call_args

    @patch("zsiga.transport.subprocess.run")
    def test_no_cd_prefix_when_cwd_none(self, mock_run):
        """Scenario: run_shell does not prefix cd when cwd is None."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0, stdout="out", stderr="")
        t = SSHTransport("host1")
        t._control_path = "/tmp/ctrl"
        t.run_shell("ls")
        call_args = mock_run.call_args[0][0]
        assert "ls" in call_args
        assert "cd" not in call_args

    @patch("zsiga.transport.subprocess.run")
    def test_returns_exit_code_minus1_on_timeout(self, mock_run):
        """Scenario: run_shell returns exit_code -1 on TimeoutExpired."""
        # First call is _ensure_control, second is the actual run_shell
        mock_run.side_effect = [
            CompletedProcess(args=[], returncode=0),
            subprocess.TimeoutExpired(cmd="ssh", timeout=120),
        ]
        t = SSHTransport("host1")
        result = t.run_shell("sleep 999", timeout=120)
        assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 120s"}

    @patch("zsiga.transport.subprocess.run")
    def test_returns_exit_code_minus1_on_generic_exception(self, mock_run):
        """Scenario: run_shell returns exit_code -1 on generic exception."""
        mock_run.side_effect = [
            CompletedProcess(args=[], returncode=0),
            OSError("connection lost"),
        ]
        t = SSHTransport("host1")
        result = t.run_shell("ls")
        assert result == {"exit_code": -1, "stdout": "", "stderr": "connection lost"}

    @patch("zsiga.transport.subprocess.run")
    def test_successful_run_returns_dict(self, mock_run):
        """SSHTransport.run_shell returns proper dict on success."""
        mock_run.side_effect = [
            CompletedProcess(args=[], returncode=0),
            CompletedProcess(args=[], returncode=0, stdout="files", stderr=""),
        ]
        t = SSHTransport("host1")
        result = t.run_shell("ls")
        assert result == {"exit_code": 0, "stdout": "files", "stderr": ""}


# ---------------------------------------------------------------------------
# SSHTransport — close
# ---------------------------------------------------------------------------


class TestSSHTransportClose:
    """SSHTransport.close sends control exit or is a no-op."""

    @patch("zsiga.transport.subprocess.run")
    def test_sends_exit_when_control_path_set(self, mock_run):
        """Scenario: close sends -O exit when control_path is set."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._control_path = "/tmp/ctrl"
        t.close()
        assert mock_run.call_count == 1
        call_args = mock_run.call_args[0][0]
        assert "-O" in call_args
        assert "exit" in call_args
        assert t._control_path is None

    @patch("zsiga.transport.subprocess.run")
    def test_no_op_when_control_path_none(self, mock_run):
        """Scenario: close is no-op when control_path is None."""
        t = SSHTransport("host1")
        t._control_path = None
        t.close()
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# create_transport factory
# ---------------------------------------------------------------------------


class TestCreateTransport:
    """create_transport returns the correct Transport subclass."""

    def test_returns_local_when_ssh_none(self):
        """Scenario: create_transport returns LocalTransport when ssh is None."""
        cfg = SimpleNamespace(ssh=None)
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_local_when_ssh_absent(self):
        """Scenario: create_transport returns LocalTransport when ssh attribute is absent."""
        cfg = SimpleNamespace()
        result = create_transport(cfg)
        assert isinstance(result, LocalTransport)

    def test_returns_ssh_when_ssh_configured(self):
        """Scenario: create_transport returns SSHTransport when ssh is configured."""
        ssh_cfg = SimpleNamespace(host="host1", user="ubuntu", port=2222, key_path="/key")
        cfg = SimpleNamespace(ssh=ssh_cfg)
        result = create_transport(cfg)
        assert isinstance(result, SSHTransport)
        assert result.host == "host1"
        assert result.user == "ubuntu"
        assert result.port == 2222
        assert result.key_path == "/key"
