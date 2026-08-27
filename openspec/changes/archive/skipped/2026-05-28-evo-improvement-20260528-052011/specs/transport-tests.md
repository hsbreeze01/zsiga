# transport-tests — Unit Test Coverage for zsiga/transport.py

## ADDED Requirements

### Requirement: Transport Abstract Base Class Contract

`Transport` SHALL define `run_shell` and `close` methods. Calling `run_shell` on the base class directly MUST raise `NotImplementedError`. Calling `close` on the base class MUST return without error.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance (the abstract base class)
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` SHALL be raised

#### Scenario: Transport.close is a no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` without raising

---

### Requirement: LocalTransport Shell Execution

`LocalTransport` SHALL delegate `run_shell` to `subprocess.run` with `shell=True`, `capture_output=True`, `text=True`, forwarding `cwd`, `timeout`, and `input` (stdin_data). It MUST return a dict with keys `exit_code`, `stdout`, `stderr`.

#### Scenario: LocalTransport.run_shell delegates to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return a `CompletedProcess(returncode=0, stdout="hello\n", stderr="")`
- **When** `run_shell("echo hello")` is called
- **Then** `subprocess.run` SHALL be called with `shell=True`, `capture_output=True`, `text=True`, and `cmd="echo hello"`
- **And** the return dict SHALL equal `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` SHALL be called with `cwd="/tmp"` and `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data as input

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("cat", stdin_data="payload")` is called
- **Then** `subprocess.run` SHALL be called with `input="payload"`

---

### Requirement: SSHTransport Initialization

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and expand `key_path` via `Path.expanduser()`. When `key_path` is `None`, it SHALL remain `None`. The `_control_path` attribute SHALL be initialized to `None`.

#### Scenario: SSHTransport.__init__ stores parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with `host="srv"`, `user="alice"`, `port=2222`, `key_path="~/.ssh/id_rsa"`
- **Then** `host` SHALL be `"srv"`, `user` SHALL be `"alice"`, `port` SHALL be `2222`, `key_path` SHALL be the expanded path of `~/.ssh/id_rsa`, and `_control_path` SHALL be `None`

#### Scenario: SSHTransport.__init__ with defaults

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with only `host="srv"`
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

---

### Requirement: SSHTransport Target Format

`_target` SHALL return `"{user}@{host}"` when `user` is set, or `host` alone when `user` is `None`.

#### Scenario: SSHTransport._target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `user="alice"`, `host="srv"`
- **When** `_target()` is called
- **Then** it SHALL return `"alice@srv"`

#### Scenario: SSHTransport._target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `user=None`, `host="srv"`
- **When** `_target()` is called
- **Then** it SHALL return `"srv"`

---

### Requirement: SSHTransport Base Arguments

`_base_args` SHALL assemble an SSH argument list starting with `["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ControlPath={control_path}"]`. When `port != 22`, it SHALL append `["-p", str(port)]`. When `key_path` is set, it SHALL append `["-i", key_path]`.

#### Scenario: SSHTransport._base_args default port no key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=22`, `key_path=None`, `_control_path="/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"StrictHostKeyChecking=no"` and `"ControlPath=/tmp/ctrl"` and SHALL NOT contain `-p` or `-i`

#### Scenario: SSHTransport._base_args custom port with key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222`, `key_path="/home/alice/.ssh/id_rsa"`, `_control_path="/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"-p"`, `"2222"`, `"-i"`, `"/home/alice/.ssh/id_rsa"`

---

### Requirement: SSHTransport Control Path Establishment

`_ensure_control` SHALL create a control master connection on first call and be idempotent on subsequent calls. On first call it MUST set `_control_path` to a temp path and invoke `subprocess.run` with SSH control master arguments. On subsequent calls (when `_control_path` is not None) it MUST return immediately without calling `subprocess.run`.

#### Scenario: SSHTransport._ensure_control creates control on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path=None`, `subprocess.run` mocked, `tempfile.mktemp` mocked to return `"/tmp/zsiga_ctrl"`
- **When** `_ensure_control()` is called
- **Then** `_control_path` SHALL be set to `"/tmp/zsiga_ctrl"`
- **And** `subprocess.run` SHALL be called once with args containing `"ControlMaster=auto"`, `"ControlPath=/tmp/zsiga_ctrl"`, `"ControlPersist=600"`

#### Scenario: SSHTransport._ensure_control is idempotent

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path` already set to `"/tmp/existing"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` SHALL NOT be called

---

### Requirement: SSHTransport Remote Shell Execution

`SSHTransport.run_shell` SHALL ensure control connection, then execute the command via SSH. When `cwd` is provided, it SHALL prepend `cd '{cwd}' &&` to the command. It MUST handle `subprocess.TimeoutExpired` by returning `{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`. It MUST handle other exceptions by returning `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: SSHTransport.run_shell executes command via SSH

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `host="srv"`, `user="alice"`, `_control_path` already set, `subprocess.run` mocked to return `CompletedProcess(returncode=0, stdout="ok", stderr="")`
- **When** `run_shell("uname")` is called
- **Then** `subprocess.run` SHALL be called with args containing `"alice@srv"` and `"uname"`
- **And** the result SHALL equal `{"exit_code": 0, "stdout": "ok", "stderr": ""}`

#### Scenario: SSHTransport.run_shell prepends cwd

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with control path established, `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/home/alice")` is called
- **Then** the last argument to `subprocess.run` SHALL be `"cd '/home/alice' && ls"`

#### Scenario: SSHTransport.run_shell handles timeout

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with control path established, `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=5)` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}`

#### Scenario: SSHTransport.run_shell handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with control path established, `subprocess.run` mocked to raise `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "network error"}`

---

### Requirement: SSHTransport Connection Teardown

`SSHTransport.close` SHALL send an SSH control exit command when `_control_path` is set, then reset `_control_path` to `None`. When `_control_path` is already `None`, it SHALL return immediately without calling `subprocess.run`.

#### Scenario: SSHTransport.close terminates control connection

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/ctrl"`, `user="alice"`, `host="srv"`, `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `"-O"`, `"exit"`, `"alice@srv"`, `"ControlPath=/tmp/ctrl"`
- **And** `_control_path` SHALL be `None`

#### Scenario: SSHTransport.close no-op without control

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None`, `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called

---

### Requirement: create_transport Factory Function

`create_transport` SHALL return a `LocalTransport` when `target_config` has no `ssh` attribute or `ssh` is falsy. It SHALL return an `SSHTransport` when `target_config.ssh` exists and is truthy, forwarding `ssh.host`, `ssh.user`, `ssh.port`, `ssh.key_path`.

#### Scenario: create_transport returns LocalTransport for no ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport for ssh config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh` attribute having `host="srv"`, `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `SSHTransport`
- **And** `host` SHALL be `"srv"`, `user` SHALL be `"alice"`, `port` SHALL be `2222`

#### Scenario: create_transport returns LocalTransport when ssh is falsy

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh=None`
- **When** `create_transport(config)` is called
- **Then** the result SHALL be an instance of `LocalTransport`
