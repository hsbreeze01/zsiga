# ssh-transport.md

## ADDED Requirements

### Requirement: SSHTransport.__init__ stores parameters and expands key_path

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, `key_path` and
initialize `_control_path` to `None`.  When `key_path` is provided it MUST be
expanded via `Path.expanduser()`.

#### Scenario: init stores host and user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport("myhost", user="alice")`
- **Then** `transport.host == "myhost"` and `transport.user == "alice"`

#### Scenario: init defaults port to 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport("myhost")`
- **Then** `transport.port == 22`

#### Scenario: init defaults key_path to None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport("myhost")`
- **Then** `transport.key_path is None`

#### Scenario: init sets control_path to None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport("myhost")`
- **Then** `transport._control_path is None`

### Requirement: SSHTransport._target builds connection string

`_target()` SHALL return `"{user}@{host}"` when `user` is set, otherwise just `host`.

#### Scenario: _target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport("myhost", user="alice")`
- **Then** `transport._target() == "alice@myhost"`

#### Scenario: _target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport("myhost")`
- **Then** `transport._target() == "myhost"`

### Requirement: SSHTransport._base_args assembles SSH arguments

`_base_args()` SHALL return a list starting with `ssh` and `StrictHostKeyChecking=no`.
It MUST include `-p {port}` when `port != 22` and `-i {key_path}` when `key_path` is set.

#### Scenario: default port 22 omits -p flag

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport("myhost")`
- **Then** `_base_args()` result does not contain `"-p"`

#### Scenario: non-default port includes -p flag

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport("myhost", port=2222)`
- **Then** `"-p"` in `_base_args()` and `"2222"` in `_base_args()`

#### Scenario: key_path includes -i flag

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport("myhost", key_path="/home/user/.ssh/id_rsa")`
- **Then** `"-i"` in `_base_args()` and the expanded key path in `_base_args()`

### Requirement: SSHTransport._ensure_control is idempotent

`_ensure_control()` SHALL create a control socket on first call and skip creation
on subsequent calls. It MUST use `tempfile.mktemp` to generate the socket path
and invoke `subprocess.run` with the master connection arguments.

#### Scenario: first call creates control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** a `SSHTransport` with `_control_path is None` and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` is set to a non-None value and `subprocess.run` was called once

#### Scenario: second call is no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** a `SSHTransport` with `_control_path` already set and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` was NOT called

### Requirement: SSHTransport.run_shell returns result dict

`SSHTransport.run_shell` SHALL call `_ensure_control()`, prepend `cd '{cwd}' &&`
when `cwd` is provided, invoke `subprocess.run` with the assembled SSH arguments,
and return `{"exit_code", "stdout", "stderr"}`.

On `subprocess.TimeoutExpired` it SHALL return `{"exit_code": -1, "stdout": "", "stderr": ...}`.
On any other `Exception` it SHALL return `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: normal execution returns result dict

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** a `SSHTransport` with `subprocess.run` mocked to return `returncode=0`,
  `stdout="out"`, `stderr="err"` and `_ensure_control` mocked
- **When** `run_shell("ls")` is called
- **Then** result is `{"exit_code": 0, "stdout": "out", "stderr": "err"}`

#### Scenario: cwd prepends cd command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** a `SSHTransport` with `subprocess.run` mocked and `_ensure_control` mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the SSH args passed to `subprocess.run` contain `"cd '/tmp' && ls"`

#### Scenario: timeout returns exit_code -1

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** a `SSHTransport` with `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
  and `_ensure_control` mocked
- **When** `run_shell("ls", timeout=5)` is called
- **Then** result `exit_code == -1` and result `stderr` contains `"Timeout"`

#### Scenario: generic exception returns exit_code -1

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** a `SSHTransport` with `subprocess.run` mocked to raise `OSError("conn refused")`
  and `_ensure_control` mocked
- **When** `run_shell("ls")` is called
- **Then** result `exit_code == -1` and result `stderr == "conn refused"`

### Requirement: SSHTransport.close sends exit command

`close()` SHALL invoke `subprocess.run` with `-O exit` to tear down the control
socket and reset `_control_path` to `None`. If `_control_path` is already `None`,
`close()` MUST be a no-op.

#### Scenario: close with active control path sends exit command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** a `SSHTransport` with `_control_path` set to a temp path and
  `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` was called with args containing `"-O"` and `"exit"`,
  and `_control_path` is now `None`

#### Scenario: close with no control path is no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** a `SSHTransport` with `_control_path is None` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` was NOT called
