# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport constructor parameter storage

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and `key_path`
attributes.  When `key_path` is provided, it MUST be expanded via
`Path.expanduser()`.  `_control_path` SHALL be initialized to `None`.

#### Scenario: SSHTransport init stores parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="srv", user="alice", port=2222, key_path="~/id_rsa")`
  is constructed
- **Then** `host` SHALL be `"srv"`, `user` SHALL be `"alice"`, `port` SHALL be `2222`,
  `key_path` SHALL equal `str(Path("~/id_rsa").expanduser())`, and `_control_path`
  SHALL be `None`

#### Scenario: SSHTransport init defaults

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="srv")` is constructed
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`,
  and `_control_path` SHALL be `None`

### Requirement: SSHTransport._base_args argument assembly

`SSHTransport._base_args` SHALL return a list starting with `ssh` and
`StrictHostKeyChecking=no`.  When `port != 22`, it MUST include `-p <port>`.
When `key_path` is set, it MUST include `-i <key_path>`.

#### Scenario: _base_args with default port and no key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** `SSHTransport(host="srv")` with `_control_path = "/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result SHALL NOT contain `-p` or `-i` flags

#### Scenario: _base_args with custom port and key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** `SSHTransport(host="srv", port=2222, key_path="/key")`
  with `_control_path = "/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"-p"`, `"2222"`, `"-i"`, `"/key"`

### Requirement: SSHTransport._target formatting

`SSHTransport._target` SHALL return `"{user}@{host}"` when `user` is set,
otherwise return `host` alone.

#### Scenario: _target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** `SSHTransport(host="srv", user="alice")`
- **When** `_target()` is called
- **Then** the result SHALL be `"alice@srv"`

#### Scenario: _target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** `SSHTransport(host="srv")`
- **When** `_target()` is called
- **Then** the result SHALL be `"srv"`

### Requirement: SSHTransport.run_shell timeout fallback

When `subprocess.run` raises `TimeoutExpired` inside `SSHTransport.run_shell`,
the method SHALL return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`.

#### Scenario: run_shell handles TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance where `_ensure_control` and
  `subprocess.run` are mocked; `subprocess.run` raises `TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=30)` is called
- **Then** the result SHALL be
  `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 30s"}`

### Requirement: SSHTransport.run_shell generic exception fallback

When `subprocess.run` raises any non-`TimeoutExpired` exception inside
`SSHTransport.run_shell`, the method SHALL return `{"exit_code": -1, "stdout": "", "stderr": "<exception message>"}`.

#### Scenario: run_shell handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance where `_ensure_control` is mocked and
  `subprocess.run` raises `RuntimeError("connection lost")`
- **When** `run_shell("cmd")` is called
- **Then** the result SHALL be
  `{"exit_code": -1, "stdout": "", "stderr": "connection lost"}`

### Requirement: SSHTransport.run_shell cwd prefix

When `cwd` is provided, `SSHTransport.run_shell` SHALL prepend
`cd '<cwd>' && ` to the remote command.

#### Scenario: run_shell prepends cwd

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance where `_ensure_control` and
  `subprocess.run` are mocked; `subprocess.run` returns a CompletedProcess
- **When** `run_shell("ls", cwd="/home/user/project")` is called
- **Then** the last argument to `subprocess.run` SHALL contain
  `"cd '/home/user/project' && ls"`

### Requirement: SSHTransport.close terminates control master

`SSHTransport.close` SHALL invoke `subprocess.run` with SSH control exit
arguments and reset `_control_path` to `None`.  If `_control_path` is already
`None`, `close` SHALL be a no-op.

#### Scenario: close terminates control master

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path = "/tmp/ctrl"` and
  `subprocess.run` is mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `"-O"`,
  `"exit"`, and `_control_path` SHALL become `None`

#### Scenario: close is no-op when no control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path = None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called and `_control_path` SHALL
  remain `None`
