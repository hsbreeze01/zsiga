# transport-test-coverage

Unit tests for `zsiga/transport.py` (96 lines, abstract base class, local
subprocess transport, SSH transport, and factory function).

---

## ADDED Requirements

### Requirement: Transport abstract base class interface

The `Transport` base class SHALL define the contract for all transport
implementations. Calling `run_shell` on the base class directly MUST raise
`NotImplementedError`. The `close` method on the base class SHALL be a
no-op (return `None`).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hello")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close returns None without error

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** the return value is `None` and no exception is raised

---

### Requirement: LocalTransport.run_shell wraps subprocess.run

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with the given
command string in shell mode, capturing stdout/stderr as text. It MUST
return a dict with exactly the keys `exit_code` (int), `stdout` (str), and
`stderr` (str).

#### Scenario: LocalTransport.run_shell executes local command

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return
  `returncode=0`, `stdout="hello\n"`, `stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result equals `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell with non-zero exit code

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return
  `returncode=42`, `stdout=""`, `stderr="fail"`
- **When** `run_shell("exit 42")` is called
- **Then** the result equals `{"exit_code": 42, "stdout": "", "stderr": "fail"}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return
  a successful result
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"` and `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return
  a successful result
- **When** `run_shell("cat", stdin_data="hello world")` is called
- **Then** `subprocess.run` is called with `input="hello world"`

---

### Requirement: SSHTransport attribute initialization

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and `key_path`
as instance attributes. `key_path` MUST be expanded via `Path.expanduser()`.
The `_control_path` attribute SHALL initially be `None`.

#### Scenario: SSHTransport stores all constructor arguments

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with `host="srv.example.com"`,
  `user="deploy"`, `port=2222`, `key_path="~/.ssh/id_rsa"`
- **When** the instance attributes are inspected
- **Then** `host` is `"srv.example.com"`, `user` is `"deploy"`,
  `port` is `2222`, `key_path` equals `str(Path("~/.ssh/id_rsa").expanduser())`,
  and `_control_path` is `None`

#### Scenario: SSHTransport defaults user to None and port to 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with only `host="srv.example.com"`
- **When** the instance attributes are inspected
- **Then** `user` is `None`, `port` is `22`, `key_path` is `None`,
  and `_control_path` is `None`

---

### Requirement: SSHTransport._base_args argument construction

`SSHTransport._base_args` SHALL return a list starting with `ssh` and
including `StrictHostKeyChecking=no`. It MUST append `-p <port>` when port
differs from 22 and `-i <key_path>` when key_path is provided.

#### Scenario: _base_args includes port and key_path flags when non-default

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222` and `key_path="/keys/id_rsa"`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"`, `"2222"`, `"-i"`, and the key_path value

#### Scenario: _base_args omits port and key_path when default

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with default `port=22` and `key_path=None`
- **When** `_base_args()` is called
- **Then** the result does NOT contain `"-p"` or `"-i"`

---

### Requirement: SSHTransport._target endpoint format

`SSHTransport._target` SHALL return `user@host` when user is set,
otherwise just `host`.

#### Scenario: _target returns user@host when user is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `user="deploy"` and `host="srv.example.com"`
- **When** `_target()` is called
- **Then** the result is `"deploy@srv.example.com"`

#### Scenario: _target returns host only when user is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `user=None` and `host="srv.example.com"`
- **When** `_target()` is called
- **Then** the result is `"srv.example.com"`

---

### Requirement: SSHTransport._ensure_control establishes ControlMaster

`_ensure_control` SHALL create a temp control socket path via
`tempfile.mktemp` and invoke `subprocess.run` to establish an SSH
ControlMaster connection. It MUST be idempotent — subsequent calls after
the first SHALL NOT invoke `subprocess.run` again.

#### Scenario: _ensure_control invokes subprocess.run on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `subprocess.run` and `tempfile.mktemp` mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is called once and `_control_path` is set to the
  value returned by `mktemp`

#### Scenario: _ensure_control is idempotent

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` whose `_control_path` is already set to a
  non-None value and `subprocess.run` is mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called

---

### Requirement: SSHTransport.run_shell remote execution

`SSHTransport.run_shell` SHALL ensure the control path, then invoke
`subprocess.run` with the SSH arguments, remote target, and the command.
It MUST return a dict with `exit_code`, `stdout`, `stderr`. When `cwd` is
provided, the remote command SHALL be prefixed with `cd '<cwd>' && `.
On `TimeoutExpired` it SHALL return `exit_code == -1` with a timeout message
in `stderr`. On any other exception it SHALL return `exit_code == -1` with
the exception message in `stderr`.

#### Scenario: SSHTransport.run_shell returns structured result on success

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run`
  mocked; `subprocess.run` returns `returncode=0`, `stdout="files"`, `stderr=""`
- **When** `run_shell("ls")` is called
- **Then** the result equals `{"exit_code": 0, "stdout": "files", "stderr": ""}`

#### Scenario: SSHTransport.run_shell prepends cwd to remote command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/home/user/project")` is called
- **Then** the last argument to `subprocess.run` contains
  `"cd '/home/user/project' && ls"`

#### Scenario: SSHTransport.run_shell handles TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked and
  `subprocess.run` raising `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result has `exit_code == -1` and `stderr` contains `"Timeout"`

#### Scenario: SSHTransport.run_shell handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked and
  `subprocess.run` raising `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result has `exit_code == -1`, `stdout == ""`, and
  `stderr == "network error"`

---

### Requirement: SSHTransport.close terminates ControlMaster

`SSHTransport.close` SHALL invoke `subprocess.run` with SSH `-O exit` to
terminate the ControlMaster connection, then reset `_control_path` to
`None`. If `_control_path` is already `None`, close SHALL be a no-op.

#### Scenario: SSHTransport.close sends exit and resets control_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path` set to `"/tmp/sock"` and
  `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with arguments containing `"-O"` and
  `"exit"`, and `_control_path` becomes `None`

#### Scenario: SSHTransport.close is no-op when control_path is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run`
  mocked
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called

---

### Requirement: create_transport factory function

`create_transport` SHALL inspect the `ssh` attribute of the provided
`target_config`. If `ssh` is falsy (None or absent), it MUST return a
`LocalTransport` instance. If `ssh` is present and truthy, it MUST return
an `SSHTransport` initialized with `ssh.host`, `ssh.user`, `ssh.port`, and
`ssh.key_path`.

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `TargetConfig` with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport when ssh config present

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `TargetConfig` with `ssh=SSHConfig(host="srv.com", user="u", port=2222, key_path="/k")`
- **When** `create_transport(target_config)` is called
- **Then** the result is an `SSHTransport` instance with `host="srv.com"`,
  `user="u"`, `port=2222`

#### Scenario: create_transport returns LocalTransport when ssh attr missing

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a plain object with no `ssh` attribute
- **When** `create_transport(obj)` is called
- **Then** the result is an instance of `LocalTransport`
