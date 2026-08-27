# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport SHALL store connection parameters on init

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, `key_path`
as instance attributes. `key_path` SHALL be expanded via `Path.expanduser()`.
`_control_path` SHALL be initialised to `None`.

#### Scenario: init stores host user port key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** no prior state
- **When** `SSHTransport(host="srv", user="alice", port=2222, key_path="~/id_rsa")` is constructed
- **Then** `host` SHALL be `"srv"`, `user` SHALL be `"alice"`, `port` SHALL be `2222`,
  `key_path` SHALL be the expanded form of `"~/id_rsa"`, and `_control_path` SHALL be `None`

#### Scenario: init with defaults for optional parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** no prior state
- **When** `SSHTransport(host="srv")` is constructed
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`,
  `_control_path` SHALL be `None`

### Requirement: SSHTransport._target SHALL format user@host or host

`_target()` SHALL return `"{user}@{host}"` when `user` is set, otherwise
just `host`.

#### Scenario: _target with user returns user at host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport(host="srv", user="alice")`
- **When** `_target()` is called
- **Then** the result SHALL be `"alice@srv"`

#### Scenario: _target without user returns host only

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport(host="srv")`
- **When** `_target()` is called
- **Then** the result SHALL be `"srv"`

### Requirement: SSHTransport._base_args SHALL build ssh argument list

`_base_args()` SHALL return a list starting with `"ssh"` and including
`StrictHostKeyChecking=no`, the `ControlPath`, `-p` when port != 22,
and `-i` when `key_path` is set.

#### Scenario: base_args with non-default port and key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport(host="srv", port=2222, key_path="/key")`
- **When** `_base_args()` is called
- **Then** the list SHALL contain `"-p", "2222"` and `"-i", "/key"`

#### Scenario: base_args with default port omits port flag

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport(host="srv", port=22)`
- **When** `_base_args()` is called
- **Then** the list SHALL NOT contain `"-p"`

### Requirement: SSHTransport._ensure_control SHALL establish ControlMaster

`_ensure_control()` SHALL set `_control_path` via `tempfile.mktemp` and
invoke `subprocess.run` to establish an SSH ControlMaster. Subsequent calls
SHALL be no-ops when `_control_path` is already set.

#### Scenario: ensure_control sets control_path and calls subprocess

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** `SSHTransport(host="srv")` with `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` SHALL be a non-None string
- **And** `subprocess.run` SHALL have been called once with args containing `"ControlMaster=auto"`

#### Scenario: ensure_control is no-op on second call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** `SSHTransport(host="srv")` with `subprocess.run` mocked and `_ensure_control()` already called once
- **When** `_ensure_control()` is called again
- **Then** `subprocess.run` SHALL have been called exactly once total

### Requirement: SSHTransport.run_shell SHALL execute remote command via SSH

`run_shell` SHALL call `_ensure_control()`, build the ssh command with
`_base_args()` + `_target()` + command, and return the standard result dict.
When `cwd` is provided, the remote command SHALL be prefixed with `cd 'cwd' &&`.
TimeoutExpired and other exceptions SHALL be caught and returned as
`exit_code=-1` with the error in `stderr`.

#### Scenario: run_shell with cwd prefixes cd command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport(host="srv")` with `subprocess.run` mocked to return
  `returncode=0, stdout="done", stderr=""`
- **When** `run_shell("ls", cwd="/app")` is called
- **Then** the ssh args passed to `subprocess.run` SHALL contain `"cd '/app' && ls"`

#### Scenario: run_shell returns exit_code minus 1 on timeout

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport(host="srv")` with `subprocess.run` mocked to raise
  `subprocess.TimeoutExpired` on the second call (the run_shell call, not ensure_control)
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result SHALL be `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}`

#### Scenario: run_shell returns exit_code minus 1 on generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport(host="srv")` with `subprocess.run` mocked to raise
  `OSError("connection refused")` on the second call
- **When** `run_shell("ls")` is called
- **Then** the result SHALL be `{"exit_code": -1, "stdout": "", "stderr": "connection refused"}`

### Requirement: SSHTransport.close SHALL terminate ControlMaster

`close()` SHALL invoke `subprocess.run` with `"-O", "exit"` to close the
SSH ControlMaster and reset `_control_path` to `None`. When `_control_path`
is already `None`, `close()` SHALL be a no-op.

#### Scenario: close with active control path terminates master

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport(host="srv")` with `_control_path` set to `"/tmp/ctrl"`
  and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL have been called with args containing `"-O", "exit"`
- **And** `_control_path` SHALL be `None`

#### Scenario: close with no control path is no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport(host="srv")` with `_control_path` is `None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT have been called
