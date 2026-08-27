# ssh-transport

## ADDED Requirements

### REQ-SSH-001: SSHTransport initialization

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and `key_path` parameters. Default values SHALL be `user=None`, `port=22`, `key_path=None`. When `key_path` contains `~`, it SHALL be expanded via `Path.expanduser()` and converted to an absolute string. The internal `_control_path` SHALL be initialized to `None`.

#### Scenario: SSHTransport stores host with defaults

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport(host="server.example.com")` is constructed
- **When** attributes are inspected
- **Then** `host == "server.example.com"`, `user is None`, `port == 22`, `key_path is None`, `_control_path is None`

#### Scenario: SSHTransport expands tilde in key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport(host="srv", key_path="~/id_rsa")` is constructed
- **When** `key_path` is inspected
- **Then** `key_path` is an absolute path string that does not start with `~`

### REQ-SSH-002: SSH target formatting

`SSHTransport._target()` SHALL return `"{user}@{host}"` when `user` is set, or `"{host}"` when `user` is `None`.

#### Scenario: _target with user returns user@host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport(host="myhost", user="admin")` instance
- **When** `_target()` is called
- **Then** the result is `"admin@myhost"`

#### Scenario: _target without user returns host only

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport(host="myhost")` instance
- **When** `_target()` is called
- **Then** the result is `"myhost"`

### REQ-SSH-003: SSH base arguments construction

`SSHTransport._base_args()` SHALL return an argument list starting with `ssh`, `StrictHostKeyChecking=no`, and `ControlPath`. It SHALL include `-p <port>` only when `port != 22`. It SHALL include `-i <key_path>` only when `key_path` is set.

#### Scenario: _base_args omits port flag for default port 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="h", port=22)` instance
- **When** `_base_args()` is called
- **Then** the result does not contain `"-p"`

#### Scenario: _base_args includes port flag for non-default port

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="h", port=2222)` instance
- **When** `_base_args()` is called
- **Then** the result contains `"-p"` followed by `"2222"`

#### Scenario: _base_args includes identity flag when key_path is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="h", key_path="/home/user/.ssh/id_rsa")` instance
- **When** `_base_args()` is called
- **Then** the result contains `"-i"` followed by `"/home/user/.ssh/id_rsa"`

### REQ-SSH-004: SSH control master management

`SSHTransport._ensure_control()` SHALL establish an SSH control master on first call by setting `_control_path` to a temp path and running `subprocess.run`. On subsequent calls, it SHALL be idempotent and NOT call `subprocess.run` again.

#### Scenario: _ensure_control calls subprocess exactly once across repeated calls

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport(host="h")` instance with `subprocess.run` mocked
- **When** `_ensure_control()` is called twice
- **Then** `subprocess.run` was called exactly once

#### Scenario: _ensure_control sets _control_path to a non-None string

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport(host="h")` instance with `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` is a non-None string

### REQ-SSH-005: SSH remote shell execution

`SSHTransport.run_shell()` SHALL first call `_ensure_control()`, then build an SSH command. When `cwd` is provided, the remote command SHALL be prefixed with `cd '<cwd>' &&`. On `subprocess.TimeoutExpired`, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after <timeout>s"}`. On any other exception, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "<exception string>"}`.

#### Scenario: run_shell with cwd prepends cd command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport(host="h", user="u")` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the SSH args contain the remote command `"cd '/tmp' && ls"`

#### Scenario: run_shell without cwd passes command directly

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport(host="h", user="u")` instance with `subprocess.run` mocked
- **When** `run_shell("ls")` is called
- **Then** the last element of the SSH args is `"ls"` (no cd prefix)

#### Scenario: run_shell returns timeout result on TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport(host="h")` instance with `subprocess.run` side_effect: first call succeeds (_ensure_control), second call raises `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": contains "Timeout after 1s"}`

### REQ-SSH-006: SSH connection cleanup

`SSHTransport.close()` SHALL send an SSH `-O exit` command to tear down the control master when `_control_path` is set, and reset `_control_path` to `None`. When `_control_path` is `None`, `close()` SHALL be a no-op and NOT call `subprocess.run`.

#### Scenario: close with active control path sends exit command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport(host="h", user="u")` instance with `_control_path="/tmp/zsiga_ssh_ctrl"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` was called with args containing `"-O"` and `"exit"`, and `_control_path` is `None`

#### Scenario: close without active control path is no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport(host="h")` instance with `_control_path=None` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` was NOT called
