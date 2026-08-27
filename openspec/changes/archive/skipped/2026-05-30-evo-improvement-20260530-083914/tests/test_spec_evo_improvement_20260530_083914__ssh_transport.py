"""Tests for zsiga/transport.py — SSHTransport detailed scenarios."""
from subprocess import CompletedProcess
from unittest.mock import patch

from zsiga.transport import SSHTransport


# ---------------------------------------------------------------------------
# SSHTransport — constructor edge cases
# ---------------------------------------------------------------------------


class TestSSHTransportInitEdge:
    """Additional constructor edge cases."""

    def test_key_path_tilde_expansion(self):
        """key_path with ~ is expanded to absolute path."""
        t = SSHTransport("h", key_path="~/.ssh/custom_key")
        assert "~" not in t.key_path
        assert t.key_path.endswith("/.ssh/custom_key")


# ---------------------------------------------------------------------------
# SSHTransport — _base_args detailed
# ---------------------------------------------------------------------------


class TestSSHTransportBaseArgsDetailed:
    """Detailed _base_args scenarios."""

    def test_base_args_starts_with_ssh(self):
        """_base_args list starts with 'ssh'."""
        t = SSHTransport("h")
        t._control_path = "/tmp/c"
        assert t._base_args()[0] == "ssh"

    def test_base_args_includes_control_path(self):
        """_base_args includes ControlPath option."""
        t = SSHTransport("h")
        t._control_path = "/tmp/ctrl_socket"
        args = t._base_args()
        assert "ControlPath=/tmp/ctrl_socket" in args


# ---------------------------------------------------------------------------
# SSHTransport — _ensure_control detailed
# ---------------------------------------------------------------------------


class TestSSHTransportEnsureControlDetailed:
    """Detailed _ensure_control scenarios."""

    @patch("zsiga.transport.subprocess.run")
    def test_control_master_args_include_target(self, mock_run):
        """_ensure_control passes target host to subprocess."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1", user="root")
        t._ensure_control()
        call_args = mock_run.call_args[0][0]
        assert "root@host1" in call_args

    @patch("zsiga.transport.subprocess.run")
    def test_control_master_args_include_control_persist(self, mock_run):
        """_ensure_control sets ControlPersist=600."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._ensure_control()
        call_args = mock_run.call_args[0][0]
        assert "ControlPersist=600" in call_args

    @patch("zsiga.transport.subprocess.run")
    def test_control_master_args_include_control_master_auto(self, mock_run):
        """_ensure_control sets ControlMaster=auto."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._ensure_control()
        call_args = mock_run.call_args[0][0]
        assert "ControlMaster=auto" in call_args

    @patch("zsiga.transport.subprocess.run")
    def test_control_master_passes_true_as_command(self, mock_run):
        """_ensure_control passes 'true' as the remote command."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._ensure_control()
        call_args = mock_run.call_args[0][0]
        assert call_args[-1] == "true"


# ---------------------------------------------------------------------------
# SSHTransport — close detailed
# ---------------------------------------------------------------------------


class TestSSHTransportCloseDetailed:
    """Detailed close scenarios."""

    @patch("zsiga.transport.subprocess.run")
    def test_close_includes_control_path_in_args(self, mock_run):
        """close includes the control_path in its SSH args."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._control_path = "/tmp/my_ctrl"
        t.close()
        call_args = mock_run.call_args[0][0]
        assert "ControlPath=/tmp/my_ctrl" in call_args

    @patch("zsiga.transport.subprocess.run")
    def test_close_resets_control_path_to_none(self, mock_run):
        """close sets _control_path to None after exit."""
        mock_run.return_value = CompletedProcess(args=[], returncode=0)
        t = SSHTransport("host1")
        t._control_path = "/tmp/ctrl"
        t.close()
        assert t._control_path is None
