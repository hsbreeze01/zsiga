# Spec: SSHTransport

## ADDED Requirements

### Requirement: SSHTransport stores connection configuration

`SSHTransport.__init__` SHALL accept `host` (required), `user` (optional), `port` (default 22), `key_path` (optional) and store them as instance attributes. When `key_path` is provided, it MUST be expanded via `Path.expanduser()`.

#### Scenario: SSHTransport.__init__ stores host and defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is initialized with `host="example.com"`
- **When** the instance attributes are inspected
- **Then** `host` SHALL be `"example.com"`, `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

#### Scenario: SSHTransport.__init__ expands key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is initialized with `host="example.com"`, `key_path="~/id_rsa"`
- **When** the `key_path` attribute is inspected
- **Then** it SHALL be the expanded absolute path (e.g. `/home/<user>/id_rsa`), not `~/id_rsa`

### Requirement: SSHTransport._target returns user@host format

`_target` SHALL return `user@host` when `user` is set, or just `host` when `user` is `None`.

#### Scenario: _target with user returns user@host

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"` and `user="admin"`
- **When** `_target()` is called
- **Then** the result SHALL be `"admin@myhost"`

#### Scenario: _target without user returns host only

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"` and `user=None`
- **When** `_target()` is called
- **Then** the result SHALL be `"myhost"`

### Requirement: SSHTransport._base_args builds SSH argument list

`_base_args` SHALL return a list starting with `"ssh"` and including `StrictHostKeyChecking=no`. It MUST append `-p <port>` when port is not 22. It MUST append `-i <key_path>` when key_path is set.

#### Scenario: _base_args with default port and no key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=22`, `key_path=None`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"ssh"` and `"StrictHostKeyChecking=no"` but NOT contain `"-p"` or `"-i"`

#### Scenario: _base_args with custom port and key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=2222`, `key_path="/key"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"-p"`, `"2222"`, `"-i"`, `"/key"`

### Requirement: SSHTransport._ensure_control establishes SSH control master

`_ensure_control` SHALL call `subprocess.run` with SSH arguments including `ControlMaster=auto` and `ControlPersist=600`. It MUST be idempotent — a second call SHALL NOT invoke subprocess again.

#### Scenario: _ensure_control calls subprocess on first invocation

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `subprocess.run` mocked
- **When** `_ensure_control()` is called for the first time
- **Then** `subprocess.run` SHALL be called once with args containing `"ControlMaster=auto"` and `"ControlPersist=600"`

#### Scenario: _ensure_control is idempotent

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `subprocess.run` mocked and `_ensure_control()` already called once
- **When** `_ensure_control()` is called again
- **Then** `subprocess.run` SHALL have been called exactly once total (not twice)

### Requirement: SSHTransport.run_shell executes remote command

`run_shell` SHALL call `_ensure_control`, build SSH args via `_base_args`, and execute the command remotely via `subprocess.run`. It SHALL prepend `cd '<cwd>' && ` to the command when `cwd` is provided. On `subprocess.TimeoutExpired`, it MUST return `{"exit_code": -1, "stderr": "Timeout after <timeout>s"}`.

#### Scenario: run_shell prepends cwd to remote command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run` mocked, and `subprocess.run` returns `returncode=0`, `stdout="ok"`, `stderr=""`
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the `subprocess.run` call args SHALL contain `"cd '/tmp' && ls"`

#### Scenario: run_shell handles timeout gracefully

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked and `subprocess.run` raising `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=5)` is called
- **Then** the result SHALL be `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}`

### Requirement: SSHTransport.close terminates control master

`close` SHALL execute `ssh -O exit` with the control path to shut down the SSH multiplexing session. If `_control_path` is `None`, `close` SHALL be a no-op.

#### Scenario: close sends exit signal to control master

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with an active control path (`_control_path` is set) and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `"-O"`, `"exit"` and `_control_path` SHALL be set to `None` afterward

#### Scenario: close is no-op without control path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called

