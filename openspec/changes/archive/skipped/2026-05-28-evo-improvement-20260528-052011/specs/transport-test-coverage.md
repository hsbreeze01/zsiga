# transport-test-coverage

## ADDED Requirements

### Requirement: Transport ABC Contract

The `Transport` abstract base class SHALL define the interface contract for all transport implementations.

- `run_shell()` SHALL raise `NotImplementedError` when called directly.
- `close()` SHALL return `None` and perform no operation.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hello")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close returns None

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** the return value is `None`

---

### Requirement: LocalTransport Shell Execution

`LocalTransport.run_shell` SHALL delegate to `subprocess.run` with `shell=True` and return a dict containing `exit_code`, `stdout`, and `stderr`.

#### Scenario: LocalTransport.run_shell delegates to subprocess and returns result dict

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return a `CompletedProcess` with `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result dict equals `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout parameters

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"` and `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data as input

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

---

### Requirement: SSHTransport Initialization

`SSHTransport.__init__` SHALL store host, user, port, key_path and expand `key_path` via `Path.expanduser()`.

#### Scenario: SSHTransport stores all parameters and expands key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="srv", user="alice", port=2222, key_path="~/id_rsa")` is constructed
- **Then** `t.host == "srv"`, `t.user == "alice"`, `t.port == 2222`, `t.key_path` equals `str(Path("~/id_rsa").expanduser())`, and `t._control_path is None`

#### Scenario: SSHTransport uses default values for user, port, key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="srv")` is constructed
- **Then** `t.user is None`, `t.port == 22`, `t.key_path is None`, `t._control_path is None`

---

### Requirement: SSHTransport Target Format

`SSHTransport._target()` SHALL return `"{user}@{host}"` when user is set, otherwise just `host`.

#### Scenario: SSHTransport._target with user returns user@host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` instance with `host="srv"` and `user="alice"`
- **When** `_target()` is called
- **Then** the result is `"alice@srv"`

#### Scenario: SSHTransport._target without user returns host only

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` instance with `host="srv"` and `user=None`
- **When** `_target()` is called
- **Then** the result is `"srv"`

---

### Requirement: SSHTransport Base Args Assembly

`SSHTransport._base_args()` SHALL assemble the SSH command-line arguments, including `-p` only when port is not 22, and `-i` only when key_path is set.

#### Scenario: SSHTransport._base_args with default port and no key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` instance with `host="srv"`, `port=22`, `key_path=None`
- **When** `_base_args()` is called
- **Then** the result does not contain `"-p"` or `"-i"`

#### Scenario: SSHTransport._base_args with custom port and key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` instance with `host="srv"`, `port=2222`, `key_path="/key"`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"`, `"2222"`, `"-i"`, `"/key"`

---

### Requirement: SSHTransport Control Master

`SSHTransport._ensure_control()` SHALL create a control master on first call and be idempotent on subsequent calls.

#### Scenario: SSHTransport._ensure_control creates control master on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` instance with `subprocess.run` and `tempfile.mktemp` mocked
- **When** `_ensure_control()` is called for the first time
- **Then** `subprocess.run` is called once with args containing `"ControlMaster=auto"`, and `_control_path` is set to the mocked tempfile value

#### Scenario: SSHTransport._ensure_control is idempotent

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` instance where `_ensure_control()` has already been called (so `_control_path` is set)
- **When** `_ensure_control()` is called again
- **Then** `subprocess.run` is not called again (total calls remain at 1 from the first invocation)

---

### Requirement: SSHTransport Remote Shell Execution

`SSHTransport.run_shell` SHALL execute commands via SSH, prefixing with `cd` when `cwd` is provided, and handle `TimeoutExpired` and general exceptions gracefully.

#### Scenario: SSHTransport.run_shell prefixes cwd into command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` and `subprocess.run` mocked, and `_control_path` already set
- **When** `run_shell("ls", cwd="/tmp/project")` is called
- **Then** the last argument to `subprocess.run` includes `"cd '/tmp/project' && ls"`

#### Scenario: SSHTransport.run_shell returns exit_code -1 on TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999")` is called
- **Then** the result dict has `exit_code == -1`

#### Scenario: SSHTransport.run_shell returns exit_code -1 and stderr on generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `subprocess.run` mocked to raise `OSError("connection lost")`
- **When** `run_shell("cmd")` is called
- **Then** the result dict has `exit_code == -1` and `"connection lost"` in `stderr`

---

### Requirement: SSHTransport Close

`SSHTransport.close()` SHALL send `-O exit` to tear down the control master when `_control_path` is set, and be a no-op otherwise.

#### Scenario: SSHTransport.close sends exit when control_path is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` instance with `_control_path` set to a non-None value and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"`, `"exit"`, and after the call `_control_path` is `None`

#### Scenario: SSHTransport.close is no-op without control_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` instance with `_control_path` set to `None`
- **When** `close()` is called
- **Then** `subprocess.run` is not called

---

### Requirement: create_transport Factory Function

`create_transport(target_config)` SHALL return a `LocalTransport` when the config has no ssh attribute or the ssh attribute is falsy, and return an `SSHTransport` when ssh is truthy with host/user/port/key_path fields.

#### Scenario: create_transport returns LocalTransport when no ssh attribute

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the returned object is an instance of `LocalTransport`

#### Scenario: create_transport returns LocalTransport when ssh is falsy

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object where `ssh` is `None`
- **When** `create_transport(config)` is called
- **Then** the returned object is an instance of `LocalTransport`

#### Scenario: create_transport returns SSHTransport when ssh is configured

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with an `ssh` attribute that has `host="srv"`, `user="alice"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the returned object is an instance of `SSHTransport` with matching `host`, `user`, `port`, `key_path`
