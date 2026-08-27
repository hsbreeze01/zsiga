# ssh-transport

## ADDED Requirements

### REQ-SSH-001: SSHTransport.__init__ SHALL store connection parameters

The constructor MUST persist all SSH connection parameters and expand
`key_path` via `Path.expanduser()`.

#### Scenario: SSHTransport stores host, user, port, key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport` is instantiated with `host="server", user="bob", port=2222, key_path="~/.ssh/id_rsa"`
- **When** attributes are inspected
- **Then** `host` SHALL equal `"server"`, `user` SHALL equal `"bob"`, `port` SHALL equal `2222`, `key_path` SHALL contain the expanded home path, and `_control_path` SHALL be `None`

#### Scenario: SSHTransport defaults user and key_path to None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport` is instantiated with only `host="server"`
- **When** attributes are inspected
- **Then** `user` SHALL be `None`, `key_path` SHALL be `None`, `port` SHALL be `22`

---

### REQ-SSH-002: SSHTransport._target SHALL format user@host or host

#### Scenario: _target returns user@host when user is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** an `SSHTransport` with `host="srv"`, `user="alice"`
- **When** `_target()` is called
- **Then** it SHALL return `"alice@srv"`

#### Scenario: _target returns host when user is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** an `SSHTransport` with `host="srv"`, `user=None`
- **When** `_target()` is called
- **Then** it SHALL return `"srv"`

---

### REQ-SSH-003: SSHTransport._base_args SHALL build SSH argument list

The argument list MUST include `StrictHostKeyChecking=no`, the control
path, optional port, and optional identity file.

#### Scenario: _base_args includes port when non-default

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** an `SSHTransport` with `port=2222`, `_control_path="/tmp/c"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"-p"` and `"2222"`

#### Scenario: _base_args includes identity file when key_path is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** an `SSHTransport` with `key_path="/home/bob/.ssh/id_rsa"`, `_control_path="/tmp/c"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"-i"` and the key path

#### Scenario: _base_args omits port when default 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** an `SSHTransport` with `port=22`, `_control_path="/tmp/c"`
- **When** `_base_args()` is called
- **Then** the result SHALL NOT contain `"-p"`

---

### REQ-SSH-004: SSHTransport._ensure_control SHALL create control master on first call

The first call MUST set `_control_path` and invoke `subprocess.run` to
establish the SSH control master. Subsequent calls SHALL skip the
setup.

#### Scenario: _ensure_control creates control path on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` SHALL be set to a non-None value starting with `"/tmp/zsiga_ssh_"` and `subprocess.run` SHALL have been called once

#### Scenario: _ensure_control skips when already connected

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** an `SSHTransport` with `_control_path="/tmp/existing"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` SHALL NOT be called and `_control_path` SHALL remain unchanged

---

### REQ-SSH-005: SSHTransport.run_shell SHALL prefix cwd and handle errors

When `cwd` is provided, the remote command MUST be prefixed with
`cd '<cwd>' &&`. Timeout and general exceptions SHALL return normalized
error dicts.

#### Scenario: run_shell with cwd prefixes cd command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run` mocked, and `subprocess.run` returns `returncode=0, stdout="out", stderr=""`
- **When** `run_shell("ls", cwd="/home")` is called
- **Then** the subprocess args SHALL include `"cd '/home' && ls"`

#### Scenario: run_shell without cwd passes command directly

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run` mocked, and `subprocess.run` returns `returncode=0, stdout="out", stderr=""`
- **When** `run_shell("ls")` is called
- **Then** the subprocess args SHALL include `"ls"` but NOT `"cd "`

#### Scenario: run_shell returns error dict on TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` with `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}`

#### Scenario: run_shell returns error dict on generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` with `subprocess.run` mocked to raise `OSError("conn refused")`
- **When** `run_shell("ls")` is called
- **Then** the result SHALL have `exit_code=-1` and `stderr` containing `"conn refused"`

---

### REQ-SSH-006: SSHTransport.close SHALL send exit signal and clear control path

#### Scenario: close sends SSH exit signal

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** an `SSHTransport` with `_control_path="/tmp/c"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `"-O", "exit"` and `_control_path` SHALL be set to `None`

#### Scenario: close is no-op when no control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** an `SSHTransport` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called
