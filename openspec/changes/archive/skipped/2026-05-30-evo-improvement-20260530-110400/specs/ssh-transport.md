# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport stores constructor parameters

`SSHTransport.__init__` SHALL persist `host`, `user`, `port`, and `key_path`
as instance attributes. The `key_path` SHALL be expanded via `Path.expanduser()`
and converted to string. The `_control_path` SHALL be initialised to `None`.

#### Scenario: SSHTransport.__init__ stores all parameters

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with `host="myhost"`, `user="alice"`,
  `port=2222`, `key_path="~/id_rsa"`
- **Then** `host` SHALL be `"myhost"`, `user` SHALL be `"alice"`,
  `port` SHALL be `2222`, `key_path` SHALL equal
  `str(Path("~/id_rsa").expanduser())`, and `_control_path` SHALL be `None`

### Requirement: SSHTransport._target formats user@host

`_target` SHALL return `"{user}@{host}"` when `user` is set, otherwise `host`
alone.

#### Scenario: _target with user returns user@host

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"` and `user="bob"`
- **When** `_target()` is called
- **Then** it SHALL return `"bob@srv"`

#### Scenario: _target without user returns host only

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"` and `user=None`
- **When** `_target()` is called
- **Then** it SHALL return `"srv"`

### Requirement: SSHTransport._base_args constructs SSH argument list

`_base_args` SHALL return a list starting with `ssh`, `-o StrictHostKeyChecking=no`,
and `-o ControlPath=<path>`. It SHALL include `-p <port>` when `port != 22` and
`-i <key_path>` when `key_path` is set.

#### Scenario: _base_args with default port and no key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=22` and `key_path=None`
- **When** `_base_args()` is called
- **Then** the result SHALL NOT contain `-p` or `-i` flags

#### Scenario: _base_args with custom port and key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222` and `key_path="/home/alice/.ssh/id_rsa"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"-p"`, `"2222"`, `"-i"`, `"/home/alice/.ssh/id_rsa"`

### Requirement: SSHTransport._ensure_control is idempotent

`_ensure_control` SHALL create a control master on first call and skip
creation on subsequent calls when `_control_path` is already set.

#### Scenario: _ensure_control is idempotent

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `subprocess.run` patched
- **When** `_ensure_control()` is called twice
- **Then** `subprocess.run` SHALL be called exactly once

### Requirement: SSHTransport.run_shell prepends cwd and handles errors

`run_shell` SHALL prepend `cd '<cwd>' && ` to the command when `cwd` is
provided. It SHALL catch `subprocess.TimeoutExpired` and return
`{"exit_code": -1, "stdout": "", "stderr": "Timeout after <timeout>s"}`.
Other exceptions SHALL return `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: run_shell with cwd prepends cd command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run` patched
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the SSH command sent to `subprocess.run` SHALL contain
  `"cd '/tmp' && ls"`

#### Scenario: run_shell handles TimeoutExpired

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` patched and
  `subprocess.run` patched to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=5)` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}`

#### Scenario: run_shell handles generic exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` patched and
  `subprocess.run` patched to raise `OSError("network down")`
- **When** `run_shell("ls")` is called
- **Then** the result `exit_code` SHALL be `-1` and `stderr` SHALL be
  `"network down"`

#### Scenario: run_shell without cwd passes command directly

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run` patched
- **When** `run_shell("ls")` is called with no `cwd`
- **Then** the SSH command SHALL be exactly `"ls"` (no `cd` prefix)

### Requirement: SSHTransport.close terminates control master

`close` SHALL send `ssh -O exit` to terminate the control master connection
and reset `_control_path` to `None`. If `_control_path` is already `None`,
`close` SHALL be a no-op.

#### Scenario: close with active control path sends exit command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path` set to `"/tmp/zsiga_ctrl"`
  and `subprocess.run` patched
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `-O` and `exit`,
  and `_control_path` SHALL be `None`

#### Scenario: close with no control path is a no-op

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path` set to `None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called

