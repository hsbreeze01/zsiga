# transport-unit-tests

## ADDED Requirements

### Requirement: Transport base class contract verification

`Transport` SHALL be an abstract base class. Calling `run_shell` on the
base class directly MUST raise `NotImplementedError`. The `close` method
SHALL be a no-op (return `None`, no side effects).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close is a no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the return value is `None`

---

### Requirement: LocalTransport shell execution

`LocalTransport` SHALL execute shell commands via `subprocess.run` and
return a dict with keys `exit_code`, `stdout`, `stderr`. All keyword
arguments (`cwd`, `timeout`, `stdin_data`) MUST be forwarded to
`subprocess.run`.

#### Scenario: LocalTransport.run_shell returns subprocess result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to
  return a `CompletedProcess` with `returncode=0`, `stdout="ok\n"`,
  `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result dict equals `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` is called with `shell=True`, `cwd="/tmp"`,
  `timeout=30`, `capture_output=True`, `text=True`

#### Scenario: LocalTransport.run_shell forwards stdin_data

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

#### Scenario: LocalTransport.close is a no-op

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.close
- **Given** a `LocalTransport` instance
- **When** `close()` is called
- **Then** no exception is raised

---

### Requirement: SSHTransport initialization

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and
`key_path` attributes. `key_path` MUST be expanded via `Path.expanduser`
and converted to a string. `_control_path` SHALL be initialized to
`None`.

#### Scenario: SSHTransport.__init__ stores parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** nothing
- **When** `SSHTransport(host="myhost", user="ubuntu", port=2222, key_path="~/.ssh/id_rsa")` is constructed
- **Then** `.host` equals `"myhost"`, `.user` equals `"ubuntu"`, `.port` equals `2222`,
  `.key_path` equals the expanded form of `~/.ssh/id_rsa`, and `._control_path` is `None`

#### Scenario: SSHTransport.__init__ defaults

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** nothing
- **When** `SSHTransport(host="myhost")` is constructed
- **Then** `.user` is `None`, `.port` is `22`, `.key_path` is `None`

---

### Requirement: SSHTransport target formatting

`_target` SHALL return `user@host` when `user` is set, or just `host`
when `user` is `None`.

#### Scenario: SSHTransport._target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport(host="h", user="u")` instance
- **When** `_target()` is called
- **Then** the result is `"u@h"`

#### Scenario: SSHTransport._target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport(host="h")` instance
- **When** `_target()` is called
- **Then** the result is `"h"`

---

### Requirement: SSHTransport base SSH arguments

`_base_args` SHALL return a list starting with `"ssh"` and including
`StrictHostKeyChecking=no`. When `port` is not `22`, a `-p` flag MUST be
included. When `key_path` is set, an `-i` flag MUST be included.

#### Scenario: SSHTransport._base_args with default port and no key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="h")` instance
- **When** `_base_args()` is called
- **Then** the result contains `"ssh"`, `"StrictHostKeyChecking=no"`, does NOT
  contain `-p`, and does NOT contain `-i`

#### Scenario: SSHTransport._base_args with custom port and key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="h", port=2222, key_path="/key")` instance
- **When** `_base_args()` is called
- **Then** the result contains `"-p"`, `"2222"`, `"-i"`, `"/key"`

---

### Requirement: SSHTransport control master setup

`_ensure_control` SHALL create a temp control path and call
`subprocess.run` with SSH control master arguments exactly once. Subsequent
calls MUST skip the setup when `_control_path` is already set.

#### Scenario: SSHTransport._ensure_control establishes control master

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport(host="h", user="u")` instance with `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` is set to a non-None value and `subprocess.run` was called
  with args containing `"ControlMaster=auto"`

#### Scenario: SSHTransport._ensure_control skips when already set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` instance where `_control_path` is already set
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called

---

### Requirement: SSHTransport shell execution

`SSHTransport.run_shell` SHALL establish the control master, execute the
command via SSH, and return a dict with `exit_code`, `stdout`, `stderr`.
When `cwd` is provided, the remote command MUST be prefixed with
`cd '<cwd>' &&`. On `subprocess.TimeoutExpired`, the result MUST contain
`exit_code=-1` and an error message in `stderr`.

#### Scenario: SSHTransport.run_shell executes command via SSH

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport(host="h", user="u")` instance with `_ensure_control`
  and `subprocess.run` mocked to return `returncode=0`, `stdout="out"`, `stderr=""`
- **When** `run_shell("ls")` is called
- **Then** the result equals `{"exit_code": 0, "stdout": "out", "stderr": ""}` and
  `subprocess.run` was called with args ending in `["u@h", "ls"]`

#### Scenario: SSHTransport.run_shell prefixes cwd

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport(host="h", user="u")` instance with `_ensure_control`
  and `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/home/user/repo")` is called
- **Then** `subprocess.run` was called with args ending in
  `["u@h", "cd '/home/user/repo' && ls"]`

#### Scenario: SSHTransport.run_shell handles timeout

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport(host="h", user="u")` instance with `_ensure_control`
  mocked and `subprocess.run` raising `TimeoutExpired`
- **When** `run_shell("sleep 999")` is called
- **Then** the result contains `exit_code=-1` and `stderr` contains `"Timeout"`

#### Scenario: SSHTransport.run_shell handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport(host="h", user="u")` instance with `_control_path` set
  and `subprocess.run` raising `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result contains `exit_code=-1` and `stderr` equals `"network error"`

---

### Requirement: SSHTransport close

`SSHTransport.close` SHALL send an SSH control exit signal when a
control path is active. When `_control_path` is `None`, `close` SHALL be
a no-op.

#### Scenario: SSHTransport.close with active control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport(host="h", user="u")` instance with `_control_path`
  set to a temp value and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` was called with args containing `"-O"`, `"exit"` and
  `_control_path` is reset to `None`

#### Scenario: SSHTransport.close with no control path is no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport(host="h")` instance with `_control_path` as `None`
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called

---

### Requirement: create_transport factory function

`create_transport` SHALL return a `LocalTransport` when the config has no
`ssh` attribute (or `ssh` is falsy). When `ssh` is present, it SHALL
return an `SSHTransport` initialized with `ssh.host`, `ssh.user`,
`ssh.port`, and `ssh.key_path`.

#### Scenario: create_transport returns LocalTransport for local config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport for ssh config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh` attribute having `host="h"`, `user="u"`,
  `port=22`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `SSHTransport` with `.host=="h"` and
  `.user=="u"`

#### Scenario: create_transport returns LocalTransport when ssh is falsy

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh=None`
- **When** `create_transport(config)` is called
- **Then** the result is an instance of `LocalTransport`
