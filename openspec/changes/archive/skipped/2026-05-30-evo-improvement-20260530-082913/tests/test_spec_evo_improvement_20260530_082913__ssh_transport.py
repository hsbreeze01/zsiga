"""Tests for spec: ssh-transport

Covers SSHTransport init, _target, _base_args, _ensure_control, run_shell, close.
"""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from zsiga.transport import SSHTransport


# ---------------------------------------------------------------------------
# SSHTransport stores host and defaults
# ---------------------------------------------------------------------------
def test_init_stores_host_and_defaults():
    """SSHTransport.__init__ stores host with default user, port, key_path."""
    t = SSHTransport(host="server.example.com")
    assert t.host == "server.example.com"
    assert t.user is None
    assert t.port == 22
    assert t.key_path is None
    assert t._control_path is None


# ---------------------------------------------------------------------------
# SSHTransport expands key_path
# ---------------------------------------------------------------------------
def test_init_expands_key_path():
    """SSHTransport.__init__ expands ~/ in key_path."""
    t = SSHTransport(host="srv", key_path="~/id_rsa")
    assert t.key_path is not None
    assert not t.key_path.startswith("~")
    assert Path(t.key_path).is_absolute()


# ---------------------------------------------------------------------------
# _target with user returns user@host
# ---------------------------------------------------------------------------
def test_target_with_user():
    """SSHTransport._target returns 'user@host' when user is set."""
    t = SSHTransport(host="myhost", user="admin")
    assert t._target() == "admin@myhost"


# ---------------------------------------------------------------------------
# _target without user returns host only
# ---------------------------------------------------------------------------
def test_target_without_user():
    """SSHTransport._target returns 'host' when user is None."""
    t = SSHTransport(host="myhost")
    assert t._target() == "myhost"


# ---------------------------------------------------------------------------
# _base_args with default port omits port flag
# ---------------------------------------------------------------------------
def test_base_args_default_port_omits_port():
    """SSHTransport._base_args omits '-p' when port is default 22."""
    t = SSHTransport(host="h", port=22)
    args = t._base_args()
    assert "-p" not in args


# ---------------------------------------------------------------------------
# _base_args with non-default port includes port flag
# ---------------------------------------------------------------------------
def test_base_args_non_default_port():
    """SSHTransport._base_args includes '-p 2222' when port=2222."""
    t = SSHTransport(host="h", port=2222)
    args = t._base_args()
    assert "-p" in args
    idx = args.index("-p")
    assert args[idx + 1] == "2222"


# ---------------------------------------------------------------------------
# _base_args with key_path includes identity flag
# ---------------------------------------------------------------------------
def test_base_args_with_key_path():
    """SSHTransport._base_args includes '-i <key_path>' when key_path is set."""
    t = SSHTransport(host="h", key_path="/home/user/.ssh/id_rsa")
    args = t._base_args()
    assert "-i" in args
    idx = args.index("-i")
    assert args[idx + 1] == "/home/user/.ssh/id_rsa"


# ---------------------------------------------------------------------------
# _ensure_control calls subprocess exactly once
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_ensure_control_calls_subprocess_once(mock_run):
    """_ensure_control calls subprocess.run exactly once across two calls."""
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    t = SSHTransport(host="h")
    t._ensure_control()
    t._ensure_control()
    assert mock_run.call_count == 1


# ---------------------------------------------------------------------------
# _ensure_control sets _control_path
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_ensure_control_sets_control_path(mock_run):
    """_ensure_control sets _control_path to a non-None string."""
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    t = SSHTransport(host="h")
    t._ensure_control()
    assert t._control_path is not None
    assert isinstance(t._control_path, str)


# ---------------------------------------------------------------------------
# run_shell with cwd prepends cd command
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_run_shell_with_cwd_prepends_cd(mock_run):
    """SSHTransport.run_shell prepends 'cd <cwd> &&' when cwd is given."""
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    t = SSHTransport(host="h", user="u")
    t.run_shell("ls", cwd="/tmp")
    # The last positional arg to subprocess.run should be the args list
    ssh_args = mock_run.call_args[0][0]
    # The last element of the SSH args is the remote command
    assert "cd '/tmp' && ls" in ssh_args


# ---------------------------------------------------------------------------
# run_shell without cwd passes command directly
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_run_shell_without_cwd_passes_command(mock_run):
    """SSHTransport.run_shell passes command directly when cwd is None."""
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    t = SSHTransport(host="h", user="u")
    t.run_shell("ls")
    ssh_args = mock_run.call_args[0][0]
    # The last element is the remote command (no cd prefix)
    assert ssh_args[-1] == "ls"


# ---------------------------------------------------------------------------
# run_shell returns timeout result on TimeoutExpired
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_run_shell_timeout_expired(mock_run):
    """SSHTransport.run_shell returns exit_code=-1 on TimeoutExpired."""
    # First call is _ensure_control, second call is the actual command
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),  # _ensure_control
        subprocess.TimeoutExpired(cmd="ssh", timeout=1),
    ]
    t = SSHTransport(host="h")
    result = t.run_shell("sleep 999", timeout=1)
    assert result["exit_code"] == -1
    assert result["stdout"] == ""
    assert "Timeout after 1s" in result["stderr"]


# ---------------------------------------------------------------------------
# close with active control path sends exit command
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_close_with_control_path_sends_exit(mock_run):
    """SSHTransport.close sends SSH -O exit when _control_path is set."""
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    t = SSHTransport(host="h", user="u")
    t._control_path = "/tmp/zsiga_ssh_ctrl"
    t.close()
    # subprocess.run should have been called once for the close
    close_call_args = mock_run.call_args[0][0]
    assert "-O" in close_call_args
    assert "exit" in close_call_args
    assert t._control_path is None


# ---------------------------------------------------------------------------
# close without active control path is no-op
# ---------------------------------------------------------------------------
@patch("zsiga.transport.subprocess.run")
def test_close_without_control_path_is_noop(mock_run):
    """SSHTransport.close does not call subprocess.run when _control_path is None."""
    t = SSHTransport(host="h")
    t.close()
    mock_run.assert_not_called()
