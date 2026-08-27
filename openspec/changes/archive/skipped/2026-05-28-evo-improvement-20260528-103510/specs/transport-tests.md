# transport-tests — Unit test coverage for zsiga/transport.py

## ADDED Requirements

### Requirement: Transport base class abstract contract

`Transport` is the abstract base for all transport backends. It SHALL define
two methods: `run_shell` and `close`.  Subclasses MUST override `run_shell`;
the default implementation raises `NotImplementedError`.  `close` is a no-op
by default.

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
- **Then** no exception is raised and the call returns `None`

---

### Requirement: LocalTransport executes local shell commands

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with `shell=True`,
forwarding `cwd`, `timeout`, and `stdin_data`, and return a dict with keys
`exit_code`, `stdout`, `stderr`.

#### Scenario: LocalTransport.run_shell returns structured result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance
- **When** `run_shell("echo hello")` is called
- **Then** the result dict has `exit_code == 0`, `stdout` contains `"hello"`,
  and `stderr == ""`

#### Scenario: LocalTransport.run_shell forwards cwd

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and a temporary directory path
- **When** `run_shell("pwd", cwd=tmp_dir)` is called
- **Then** `stdout` contains the temporary directory path

#### Scenario: LocalTransport.run_shell forwards stdin_data

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance
- **When** `run_shell("cat", stdin_data="payload")` is called
- **Then** `stdout` equals `"payload"`

#### Scenario: LocalTransport.run_shell reports non-zero exit code

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance
- **When** `run_shell("exit 42")` is called
- **Then** `exit_code == 42`

---

### Requirement: SSHTransport manages SSH multiplexed connections

`SSHTransport` SHALL manage an SSH ControlMaster for connection reuse.
It stores connection parameters on construction, lazily establishes a control
socket on first `run_shell` call, and tears it down on `close`.

#### Scenario: SSHTransport.__init__ stores host and defaults

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is constructed with `host="myhost"`
- **When** the instance attributes are inspected
- **Then** `host == "myhost"`, `user is None`, `port == 22`,
  `key_path is None`, `_control_path is None`

#### Scenario: SSHTransport.__init__ expands key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is constructed with `host="h", key_path="~/id_rsa"`
- **When** `key_path` attribute is read
- **Then** it contains the expanded home directory path (no leading `~`)

#### Scenario: SSHTransport._target returns user@host or host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"` and `user="bob"`
- **When** `_target()` is called
- **Then** result is `"bob@myhost"`

#### Scenario: SSHTransport._target returns host without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"` and `user=None`
- **When** `_target()` is called
- **Then** result is `"myhost"`

#### Scenario: SSHTransport._base_args includes StrictHostKeyChecking=no

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=22`, `key_path=None`
- **When** `_base_args()` is called
- **Then** the result list contains `"StrictHostKeyChecking=no"`

#### Scenario: SSHTransport._base_args adds -p for non-default port

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=2222`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"` followed by `"2222"`

#### Scenario: SSHTransport._base_args omits -p for default port 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=22`
- **When** `_base_args()` is called
- **Then** `"-p"` is NOT in the result list

#### Scenario: SSHTransport._base_args adds -i for key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `key_path="/home/bob/.ssh/key"`
- **When** `_base_args()` is called
- **Then** the result contains `"-i"` followed by `"/home/bob/.ssh/key"`

#### Scenario: SSHTransport._ensure_control skips when already established

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path` already set to `"/tmp/ctrl"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called (no new SSH connection)

#### Scenario: SSHTransport._ensure_control creates control master

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path is None` and
  `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is called with args containing
  `"ControlMaster=auto"` and `_control_path` is set to a non-None value

#### Scenario: SSHTransport.run_shell prepends cd when cwd given

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with mocked `subprocess.run` returning success
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the command passed to SSH contains `"cd '/tmp' && ls"`

#### Scenario: SSHTransport.run_shell handles TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with mocked `subprocess.run` that raises
  `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999")` is called
- **Then** result has `exit_code == -1` and `stderr` contains `"Timeout"`

#### Scenario: SSHTransport.run_shell handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with mocked `subprocess.run` that raises
  `OSError("connection lost")`
- **When** `run_shell("cmd")` is called
- **Then** result has `exit_code == -1` and `stderr == "connection lost"`

#### Scenario: SSHTransport.close sends exit to control master

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path` set and
  `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"` and `"exit"`,
  and `_control_path` becomes `None`

#### Scenario: SSHTransport.close is no-op without control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path is None` and
  `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called

---

### Requirement: create_transport factory returns correct backend

`create_transport(target_config)` SHALL inspect the config for an `ssh`
attribute.  If absent or falsy, it returns `LocalTransport`.  If present, it
returns `SSHTransport` populated from `ssh.host`, `ssh.user`, `ssh.port`,
`ssh.key_path`.

#### Scenario: create_transport returns LocalTransport when no ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the result is a `LocalTransport` instance

#### Scenario: create_transport returns LocalTransport when ssh is falsy

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh = None`
- **When** `create_transport(config)` is called
- **Then** the result is a `LocalTransport` instance

#### Scenario: create_transport returns SSHTransport when ssh present

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with an `ssh` attribute having `host="myhost"`,
  `user="bob"`, `port=2222`, `key_path="/key"`
- **When** `create_transport(config)` is called
- **Then** the result is an `SSHTransport` with `host="myhost"`,
  `user="bob"`, `port=2222`
