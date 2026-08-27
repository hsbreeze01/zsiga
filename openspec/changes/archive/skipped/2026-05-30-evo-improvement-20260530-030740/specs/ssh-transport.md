# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport Initialization
`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and `key_path` as
instance attributes. `key_path` MUST be expanded via `Path.expanduser()` when
provided. Default values SHALL be `user=None`, `port=22`, `key_path=None`.
The `_control_path` attribute MUST be initialized to `None`.

#### Scenario: SSHTransport stores all constructor parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport("myhost", user="alice", port=2222, key_path="~/.ssh/id_rsa")`
- **When** the instance is constructed
- **Then** `host` is `"myhost"`, `user` is `"alice"`, `port` is `2222`,
  `key_path` is the expanded form of `~/.ssh/id_rsa`, and `_control_path` is `None`

#### Scenario: SSHTransport uses default parameter values

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport("myhost")`
- **When** the instance is constructed
- **Then** `user` is `None`, `port` is `22`, `key_path` is `None`,
  `_control_path` is `None`

### Requirement: SSHTransport Target String
`_target()` SHALL return `"user@host"` when `user` is set, otherwise just `"host"`.

#### Scenario: _target returns user@host when user is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport("myhost", user="alice")` instance
- **When** `_target()` is called
- **Then** the result is `"alice@myhost"`

#### Scenario: _target returns bare host when user is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport("myhost")` instance (no user)
- **When** `_target()` is called
- **Then** the result is `"myhost"`

### Requirement: SSHTransport Base SSH Arguments
`_base_args()` SHALL return a list beginning with `"ssh"` and including
`StrictHostKeyChecking=no` and the `ControlPath` option. It MUST include `-p`
and the port number only when `port != 22`. It MUST include `-i` and the
`key_path` only when `key_path` is not `None`.

#### Scenario: _base_args omits port flag when port is 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport("myhost")` instance (default port 22)
- **When** `_base_args()` is called
- **Then** the returned list does not contain `"-p"`

#### Scenario: _base_args includes port flag when port is not 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport("myhost", port=2222)` instance
- **When** `_base_args()` is called
- **Then** the returned list contains `"-p"` followed by `"2222"`

#### Scenario: _base_args includes identity flag when key_path is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport("myhost", key_path="/home/me/.ssh/id_rsa")` instance
- **When** `_base_args()` is called
- **Then** the returned list contains `"-i"` followed by the key_path value

#### Scenario: _base_args omits identity flag when key_path is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport("myhost")` instance (no key_path)
- **When** `_base_args()` is called
- **Then** the returned list does not contain `"-i"`

### Requirement: SSHTransport Control Path Management
`_ensure_control()` SHALL create a control path on first call via
`tempfile.mktemp` and execute an SSH control master setup command. Subsequent
calls MUST be idempotent (no new subprocess call). `close()` SHALL send an
SSH `-O exit` command via the control path and reset `_control_path` to `None`.
If `_control_path` is `None` when `close()` is called, it MUST be a no-op.

#### Scenario: _ensure_control establishes control path on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport("myhost")` instance with `subprocess.run` mocked,
  and `_control_path` is `None`
- **When** `_ensure_control()` is called
- **Then** `_control_path` is set to a non-None value and `subprocess.run` is
  called once with arguments containing `"ControlMaster=auto"`

#### Scenario: _ensure_control is idempotent on subsequent calls

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport("myhost")` instance where `_ensure_control()` has
  already been called once
- **When** `_ensure_control()` is called again
- **Then** `subprocess.run` is not called again (total call count remains 1)

#### Scenario: close sends exit signal when control path is active

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport("myhost")` instance with an active control path
  (after `_ensure_control()`), and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with arguments containing `"-O"` and
  `"exit"`, and `_control_path` becomes `None`

#### Scenario: close is no-op when no control path exists

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** a freshly constructed `SSHTransport("myhost")` instance
  (`_control_path` is `None`), with `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is not called and `_control_path` remains `None`

### Requirement: SSHTransport Remote Shell Execution
`run_shell()` SHALL call `_ensure_control()`, then execute the given command
over SSH. When `cwd` is provided, the remote command MUST be prefixed with
`cd '<cwd>' && `. On `subprocess.TimeoutExpired`, it MUST return
`{"exit_code": -1, "stdout": "", "stderr": "Timeout after <timeout>s"}`.
On any other exception, it MUST return `{"exit_code": -1, "stdout": "",
"stderr": "<exception message>"}`.

#### Scenario: run_shell executes command via SSH

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport("myhost")` instance with `subprocess.run` mocked
  to return `returncode=0`, `stdout="out"`, `stderr=""`
- **When** `run_shell("whoami")` is called
- **Then** the result is `{"exit_code": 0, "stdout": "out", "stderr": ""}` and
  `subprocess.run` was called with args containing the remote target

#### Scenario: run_shell prefixes cwd into remote command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport("myhost")` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/var/log")` is called
- **Then** `subprocess.run` is called with args containing
  `"cd '/var/log' && ls"`

#### Scenario: run_shell handles TimeoutExpired gracefully

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport("myhost")` instance with `subprocess.run` mocked
  to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}`

#### Scenario: run_shell handles generic exception gracefully

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport("myhost")` instance with `subprocess.run` mocked
  to raise `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result dict has `exit_code` equal to `-1` and `stderr` equal to
  `"network error"`
