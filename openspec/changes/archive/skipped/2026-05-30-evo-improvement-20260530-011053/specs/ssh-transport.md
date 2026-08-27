# ssh-transport.md

## ADDED Requirements

### Requirement: SSHTransport Initialization

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and `key_path`.
`key_path` MUST be expanded via `Path.expanduser()` and converted to string.
`_control_path` SHALL be initialized to `None`.

#### Scenario: SSHTransport.__init__ stores all parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no prior state
- **When** `SSHTransport(host="srv", user="bob", port=2222, key_path="~/.ssh/id")`
    is constructed
- **Then** `host` MUST be `"srv"`, `user` MUST be `"bob"`, `port` MUST be `2222`,
    `key_path` MUST be the expanded path string, and `_control_path` MUST be `None`

#### Scenario: SSHTransport.__init__ uses defaults for optional params

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no prior state
- **When** `SSHTransport(host="srv")` is constructed
- **Then** `user` MUST be `None`, `port` MUST be `22`, `key_path` MUST be `None`,
    and `_control_path` MUST be `None`

### Requirement: SSHTransport Target Address

`_target()` SHALL return `user@host` when `user` is set, or `host` alone when
`user` is `None`.

#### Scenario: _target returns user@host when user is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"` and `user="alice"`
- **When** `_target()` is called
- **Then** it MUST return `"alice@srv"`

#### Scenario: _target returns host when user is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"` and `user=None`
- **When** `_target()` is called
- **Then** it MUST return `"srv"`

### Requirement: SSHTransport Base Arguments

`_base_args()` SHALL construct the SSH command-line argument list including
`StrictHostKeyChecking=no` and `ControlPath`. It MUST include `-p` when port is
not 22, and MUST include `-i` when `key_path` is set.

#### Scenario: _base_args includes default options

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="srv")` with default port 22 and no key_path
- **When** `_base_args()` is called
- **Then** the result MUST contain `"ssh"`, `"StrictHostKeyChecking=no"`, and
    MUST NOT contain `"-p"` or `"-i"`

#### Scenario: _base_args adds port when non-default

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="srv", port=2222)`
- **When** `_base_args()` is called
- **Then** the result MUST contain `"-p"` followed by `"2222"`

#### Scenario: _base_args adds identity when key_path set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport(host="srv", key_path="/home/me/.ssh/id")`
- **When** `_base_args()` is called
- **Then** the result MUST contain `"-i"` followed by the key path

### Requirement: SSHTransport ControlMaster Management

`_ensure_control()` SHALL create an SSH ControlMaster on first call and skip on
subsequent calls. It MUST use `ControlMaster=auto`, `ControlPersist=600`, and
execute `true` on the remote host.

#### Scenario: _ensure_control creates control master on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` instance with `_control_path=None` and
    `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` MUST be set to a non-None value, and `subprocess.run`
    MUST be called with args containing `"ControlMaster=auto"` and `"ControlPersist=600"`

#### Scenario: _ensure_control skips when already initialized

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` instance with `_control_path` already set to a value
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` MUST NOT be called

### Requirement: SSHTransport Remote Command Execution

`run_shell` SHALL execute commands on the remote host via SSH. When `cwd` is
provided, it MUST prepend `cd '<cwd>' &&` to the command. It SHALL handle
`subprocess.TimeoutExpired` by returning `exit_code=-1` with a timeout message
in stderr. It SHALL handle other exceptions by returning `exit_code=-1` with
the exception string in stderr.

#### Scenario: run_shell executes remote command and returns result

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `subprocess.run` mocked to return
    `returncode=0`, `stdout="out"`, `stderr=""`
- **When** `run_shell("ls")` is called
- **Then** the result MUST be `{"exit_code": 0, "stdout": "out", "stderr": ""}`
    and `_ensure_control` MUST have been called

#### Scenario: run_shell prepends cd when cwd is provided

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` mocked and
    `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the last argument to `subprocess.run` MUST contain
    `"cd '/tmp' && ls"`

#### Scenario: run_shell handles TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` mocked and
    `subprocess.run` raising `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result MUST have `exit_code=-1` and `stderr` MUST contain
    `"Timeout"`

#### Scenario: run_shell handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` instance with `_ensure_control` mocked and
    `subprocess.run` raising `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result MUST have `exit_code=-1` and `stderr` MUST contain
    `"network error"`

### Requirement: SSHTransport Connection Close

`close()` SHALL close the SSH ControlMaster by sending `"-O" "exit"` via SSH
when `_control_path` is set. When `_control_path` is `None`, `close()` MUST be
a no-op.

#### Scenario: close sends exit command when control path is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` instance with `_control_path="/tmp/ctrl"` and
    `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` MUST be called with args containing `"-O"` and
    `"exit"`, and `_control_path` MUST be reset to `None`

#### Scenario: close is a no-op when control path is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` instance with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` MUST NOT be called and `_control_path` MUST remain
    `None`
