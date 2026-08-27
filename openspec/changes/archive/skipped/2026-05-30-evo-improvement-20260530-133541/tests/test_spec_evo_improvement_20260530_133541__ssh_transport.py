"""Tests for ssh-transport spec — SSHTransport remote command execution."""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from zsiga.transport import SSHTransport


def test_init_host_only_stores_defaults():
    """Init with host-only stores defaults."""
    t = SSHTransport(host="server.example.com")
    assert t.host == "server.example.com"
    assert t.user is None
    assert t.port == 22
    assert t.key_path is None
    assert t._control_path is None


def test_init_with_full_parameters():
    """Init with full parameters stores all values."""
    t = SSHTransport(host="srv", user="alice", port=2222, key_path="~/.ssh/id_rsa")
    assert t.host == "srv"
    assert t.user == "alice"
    assert t.port == 2222
    expected_key = str(Path("~/.ssh/id_rsa").expanduser())
    assert t.key_path == expected_key
    assert t._control_path is None


def test_target_with_user():
    """_target with user returns user@host."""
    t = SSHTransport(host="srv", user="alice")
    assert t._target() == "alice@srv"


def test_target_without_user():
    """_target without user returns host only."""
    t = SSHTransport(host="srv")
    assert t._target() == "srv"


def test_base_args_default_port_no_key():
    """_base_args with default port and no key omits -p and -i."""
    t = SSHTransport(host="srv", port=22, key_path=None)
    t._control_path = "/tmp/ctrl"
    args = t._base_args()
    assert "-p" not in args
    assert "-i" not in args


def test_base_args_custom_port_and_key():
    """_base_args with custom port and key includes port and key flags."""
    t = SSHTransport(host="srv", port=2222, key_path="/home/alice/.ssh/id")
    t._control_path = "/tmp/ctrl"
    args = t._base_args()
    assert "-p" in args
    assert "2222" in args
    assert "-i" in args
    assert "/home/alice/.ssh/id" in args


def test_run_shell_with_cwd_prepends_cd():
    """run_shell with cwd prepends cd command."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    t = SSHTransport(host="srv", user="alice")
    t._control_path = "/tmp/ctrl"

    with patch("zsiga.transport.subprocess.run", return_value=mock_result) as mock_run:
        t.run_shell("ls", cwd="/home")

    # Last arg to subprocess.run should contain the cd && command
    call_args = mock_run.call_args
    last_arg = call_args[0][0][-1]
    assert last_arg == "cd '/home' && ls"


def test_run_shell_without_cwd_does_not_prepend_cd():
    """run_shell without cwd does not prepend cd."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    t = SSHTransport(host="srv", user="alice")
    t._control_path = "/tmp/ctrl"

    with patch("zsiga.transport.subprocess.run", return_value=mock_result) as mock_run:
        t.run_shell("ls")

    call_args = mock_run.call_args
    last_arg = call_args[0][0][-1]
    assert last_arg == "ls"


def test_run_shell_handles_timeout():
    """run_shell handles subprocess timeout."""
    t = SSHTransport(host="srv", user="alice")
    t._control_path = "/tmp/ctrl"

    with patch("zsiga.transport.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=5)):
        result = t.run_shell("sleep 999", timeout=5)

    assert result == {"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}


def test_run_shell_handles_generic_exception():
    """run_shell handles generic exception."""
    t = SSHTransport(host="srv", user="alice")
    t._control_path = "/tmp/ctrl"

    with patch("zsiga.transport.subprocess.run", side_effect=OSError("connection refused")):
        result = t.run_shell("ls")

    assert result["exit_code"] == -1
    assert result["stdout"] == ""
    assert "connection refused" in result["stderr"]


def test_close_with_active_control_path():
    """close with active control path sends exit command."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    t = SSHTransport(host="srv", user="alice")
    t._control_path = "/tmp/zsiga_ssh_abc"

    with patch("zsiga.transport.subprocess.run", return_value=mock_result) as mock_run:
        t.close()

    call_args = mock_run.call_args
    args_list = call_args[0][0]
    assert "-O" in args_list
    assert "exit" in args_list
    assert t._control_path is None


def test_close_with_no_control_path_is_noop():
    """close with no control path is a no-op."""
    t = SSHTransport(host="srv", user="alice")
    t._control_path = None

    with patch("zsiga.transport.subprocess.run") as mock_run:
        t.close()

    mock_run.assert_not_called()
    assert t._control_path is None
