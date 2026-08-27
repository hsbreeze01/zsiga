# transport-classes

## ADDED Requirements

### Requirement: Transport base class run_shell raises NotImplementedError

`Transport` SHALL act as a base class for transport implementations. Calling
`run_shell` on the base class directly MUST raise `NotImplementedError`.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("ls")` is called
- **Then** `NotImplementedError` is raised

---

### Requirement: Transport base class close is no-op

`Transport.close()` SHALL be a safe no-op that returns `None` and raises no
exception.

#### Scenario: Transport.close returns None without error

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the return value is `None`

---

### Requirement: LocalTransport.run_shell delegates to subprocess.run

`LocalTransport.run_shell(cmd)` SHALL invoke `subprocess.run` with `shell=True`,
`capture_output=True`, `text=True`, and forward all keyword arguments (`cwd`,
`timeout`, `input`). It MUST return a dict with keys `exit_code`, `stdout`,
`stderr` populated from the `CompletedProcess` result.

#### Scenario: LocalTransport.run_shell returns exit_code stdout stderr dict

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  a `CompletedProcess` with `returncode=0`, `stdout="ok"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result is `{"exit_code": 0, "stdout": "ok", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"` and `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data as input

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

---

### Requirement: LocalTransport.close is no-op

`LocalTransport` inherits `close()` from `Transport` and SHALL NOT perform any
side-effect.

#### Scenario: LocalTransport.close does not raise

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.close
- **Given** a `LocalTransport` instance
- **When** `close()` is called
- **Then** no exception is raised

---

### Requirement: SSHTransport stores configuration on init

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, `key_path` as
instance attributes. `key_path` MUST be expanded via `Path.expanduser()`.
`_control_path` SHALL be initialised to `None`.

#### Scenario: SSHTransport stores host user port key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is initialised with `host="srv"`, `user="bob"`,
  `port=2222`, `key_path="~/keys/id_rsa"`
- **Then** `instance.host == "srv"`, `instance.user == "bob"`,
  `instance.port == 2222`, `instance.key_path` is the expanded path,
  `instance._control_path is None`

---

### Requirement: SSHTransport._target formats user@host

`_target()` SHALL return `user@host` when `user` is set, or just `host` when
`user` is `None`.

#### Scenario: _target with user returns user@host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"`, `user="bob"`
- **When** `_target()` is called
- **Then** the result is `"bob@srv"`

#### Scenario: _target without user returns host only

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"`, `user=None`
- **When** `_target()` is called
- **Then** the result is `"srv"`

---

### Requirement: SSHTransport._base_args builds SSH argument list

`_base_args()` SHALL return a list starting with `"ssh"`, including
`StrictHostKeyChecking=no`, the `ControlPath`, optional `-p port` when port is
not 22, and optional `-i key_path` when `key_path` is set.

#### Scenario: _base_args includes port when non-default

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222` and `_control_path="/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"` and `"2222"`

#### Scenario: _base_args omits port when default 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=22` and `_control_path="/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result does NOT contain `"-p"`

#### Scenario: _base_args includes identity flag when key_path set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `key_path="/home/bob/.ssh/id_rsa"` and
  `_control_path="/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result contains `"-i"` and the expanded key_path string

---

### Requirement: SSHTransport._ensure_control establishes SSH multiplexing

On first call, `_ensure_control()` SHALL create a temp control-path, call
`subprocess.run` with SSH `ControlMaster=auto` arguments, and store the path.
Subsequent calls with an already-set `_control_path` MUST be no-ops.

#### Scenario: _ensure_control creates control master on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path=None` and
  `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is called with args containing
  `"ControlMaster=auto"` and `"true"`, and `_control_path` is set to a non-None
  value

#### Scenario: _ensure_control skips when control path already set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path="/tmp/existing"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called

---

### Requirement: SSHTransport.run_shell executes remote command via SSH

`run_shell` SHALL call `_ensure_control`, build the SSH command via
`_base_args` + `_target` + command, and invoke `subprocess.run`. When `cwd` is
provided, the remote command MUST be prefixed with `cd '<cwd>' &&`. On
`TimeoutExpired` it SHALL return `exit_code=-1` with timeout message. On other
exceptions it SHALL return `exit_code=-1` with the exception string as stderr.

#### Scenario: run_shell prepends cwd to remote command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `subprocess.run` mocked to return
  `returncode=0`, `stdout="out"`, `stderr=""`
- **When** `run_shell("ls", cwd="/home")` is called
- **Then** the last argument to `subprocess.run` contains `"cd '/home' && ls"`

#### Scenario: run_shell returns exit_code -1 on timeout

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `subprocess.run` mocked to raise
  `subprocess.TimeoutExpired("cmd", 120)`
- **When** `run_shell("ls")` is called
- **Then** the result dict has `exit_code == -1` and `stderr` contains
  `"Timeout"`

#### Scenario: run_shell returns exit_code -1 on generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `subprocess.run` mocked to raise
  `OSError("connection lost")`
- **When** `run_shell("ls")` is called
- **Then** the result dict has `exit_code == -1` and `stderr == "connection lost"`

---

### Requirement: SSHTransport.close sends SSH control exit

When `_control_path` is set, `close()` SHALL invoke `subprocess.run` with
`ssh -O exit` and the control path, then reset `_control_path` to `None`. When
`_control_path` is `None`, `close()` SHALL be a no-op.

#### Scenario: close sends exit and resets control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/ctrl"` and
  `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"` and `"exit"`,
  and `_control_path` is `None`

#### Scenario: close is no-op without control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called
