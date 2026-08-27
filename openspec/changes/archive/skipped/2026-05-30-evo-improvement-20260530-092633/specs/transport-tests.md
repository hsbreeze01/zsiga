# transport-tests — Delta Spec

## ADDED Requirements

### Requirement: Transport base class contract

`Transport` SHALL define the interface contract for all transport implementations. `run_shell()` SHALL raise `NotImplementedError`. `close()` SHALL return `None`.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` base class instance
- **When** `run_shell("echo hello")` is called
- **Then** it SHALL raise `NotImplementedError`

#### Scenario: Transport.close returns None

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` base class instance
- **When** `close()` is called
- **Then** it SHALL return `None`

---

### Requirement: LocalTransport subprocess delegation

`LocalTransport.run_shell()` SHALL delegate to `subprocess.run` with `shell=True`, `capture_output=True`, `text=True`, and forward `cwd`, `timeout`, `stdin_data` (as `input`). It SHALL return a dict with keys `exit_code`, `stdout`, `stderr`.

#### Scenario: LocalTransport.run_shell forwards correct subprocess args

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `CompletedProcess(returncode=0, stdout="ok\n", stderr="")`
- **When** `run_shell("ls -la", cwd="/tmp", timeout=60, stdin_data="hello")` is called
- **Then** the mock SHALL be called with `shell=True, cwd="/tmp", capture_output=True, text=True, timeout=60, input="hello"`
- **And** the result SHALL equal `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell returns nonzero exit_code

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `CompletedProcess(returncode=127, stdout="", stderr="command not found")`
- **When** `run_shell("badcmd")` is called
- **Then** the result SHALL equal `{"exit_code": 127, "stdout": "", "stderr": "command not found"}`

#### Scenario: LocalTransport.run_shell with default parameters

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `CompletedProcess(returncode=0, stdout="done", stderr="")`
- **When** `run_shell("echo done")` is called with no optional arguments
- **Then** the mock SHALL be called with `cwd=None, timeout=120, input=None`
- **And** the result SHALL equal `{"exit_code": 0, "stdout": "done", "stderr": ""}`

---

### Requirement: SSHTransport initialisation and control path

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, `key_path` (with `Path.expanduser`), and initialise `_control_path` to `None`. `_target()` SHALL return `user@host` when user is set, or just `host` otherwise. `_base_args()` SHALL construct the SSH argument list with `StrictHostKeyChecking=no`, optional port (`-p`), and optional identity (`-i`).

#### Scenario: SSHTransport.__init__ with all parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="myhost", user="alice", port=2222, key_path="~/.ssh/id_rsa")` is constructed
- **Then** `host` SHALL be `"myhost"`, `user` SHALL be `"alice"`, `port` SHALL be `2222`, `key_path` SHALL be the expanded path of `~/.ssh/id_rsa`, `_control_path` SHALL be `None`

#### Scenario: SSHTransport._target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` instance with `host="srv"` and `user="bob"`
- **When** `_target()` is called
- **Then** it SHALL return `"bob@srv"`

#### Scenario: SSHTransport._target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` instance with `host="srv"` and `user=None`
- **When** `_target()` is called
- **Then** it SHALL return `"srv"`

#### Scenario: SSHTransport._base_args default port no key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` instance with `host="srv"`, `port=22`, `key_path=None`, `_control_path="/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result SHALL NOT contain `-p` or `-i` flags

#### Scenario: SSHTransport._base_args custom port and key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` instance with `host="srv"`, `port=2222`, `key_path="/home/user/.ssh/key"`, `_control_path="/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `-p`, `2222`, `-i`, `/home/user/.ssh/key`

---

### Requirement: SSHTransport.run_shell execution

`SSHTransport.run_shell()` SHALL call `_ensure_control()`, build the command string (prepending `cd '<cwd>' &&` if `cwd` is provided), and delegate to `subprocess.run`. On `subprocess.TimeoutExpired` it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after <timeout>s"}`. On any other exception it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "<exception string>"}`.

#### Scenario: SSHTransport.run_shell normal execution

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` mocked to no-op, and `subprocess.run` mocked to return `CompletedProcess(returncode=0, stdout="out", stderr="")`
- **When** `run_shell("ls")` is called
- **Then** the result SHALL equal `{"exit_code": 0, "stdout": "out", "stderr": ""}`

#### Scenario: SSHTransport.run_shell with cwd prepends cd

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` mocked to no-op, and `subprocess.run` mocked to return `CompletedProcess(returncode=0, stdout="", stderr="")`
- **When** `run_shell("ls", cwd="/home/user")` is called
- **Then** the last argument to `subprocess.run` SHALL be `"cd '/home/user' && ls"`

#### Scenario: SSHTransport.run_shell timeout returns exit_code -1

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` mocked to no-op, and `subprocess.run` mocked to raise `subprocess.TimeoutExpired("cmd", 30)`
- **When** `run_shell("sleep 999", timeout=30)` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 30s"}`

#### Scenario: SSHTransport.run_shell generic exception returns exit_code -1

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` mocked to no-op, and `subprocess.run` mocked to raise `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "network error"}`

---

### Requirement: SSHTransport control path lifecycle

`_ensure_control()` SHALL be idempotent — if `_control_path` is already set, it SHALL return immediately without calling `subprocess.run`. `close()` SHALL send `-O exit` via SSH to tear down the control master and reset `_control_path` to `None`. If `_control_path` is `None`, `close()` SHALL return immediately without calling `subprocess.run`.

#### Scenario: SSHTransport._ensure_control idempotent

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` instance with `_control_path` already set to `/tmp/existing`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` SHALL NOT be called and `_control_path` SHALL remain `/tmp/existing`

#### Scenario: SSHTransport._ensure_control first call sets control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` instance with `_control_path=None`, `tempfile.mktemp` mocked to return `/tmp/zsiga_ctrl`, and `subprocess.run` mocked to return `CompletedProcess(returncode=0, stdout="", stderr="")`
- **When** `_ensure_control()` is called
- **Then** `_control_path` SHALL be `/tmp/zsiga_ctrl`
- **And** `subprocess.run` SHALL be called once with args containing `ControlMaster=auto` and `ControlPersist=600`

#### Scenario: SSHTransport.close sends exit command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` instance with `_control_path="/tmp/ctrl"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `-O` and `exit`
- **And** `_control_path` SHALL be `None`

#### Scenario: SSHTransport.close with no control path is no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` instance with `_control_path=None` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called

---

### Requirement: create_transport factory function

`create_transport(target_config)` SHALL return `LocalTransport` when `target_config` has no `ssh` attribute or `ssh` is falsy. It SHALL return `SSHTransport` when `target_config.ssh` is truthy, forwarding `ssh.host`, `ssh.user`, `ssh.port`, `ssh.key_path`.

#### Scenario: create_transport returns LocalTransport when no ssh config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` with no `ssh` attribute
- **When** `create_transport(target_config)` is called
- **Then** it SHALL return a `LocalTransport` instance

#### Scenario: create_transport returns LocalTransport when ssh is None

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` with `ssh=None`
- **When** `create_transport(target_config)` is called
- **Then** it SHALL return a `LocalTransport` instance

#### Scenario: create_transport returns SSHTransport when ssh is configured

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a `target_config` with `ssh` having `host="myhost"`, `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(target_config)` is called
- **Then** it SHALL return an `SSHTransport` instance with `host="myhost"`, `user="alice"`, `port=2222`, `key_path="/key"`
