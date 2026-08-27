# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport initialization

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and `key_path`
parameters as instance attributes. When `key_path` is provided it SHALL be
expanded via `Path.expanduser()` and converted to `str`. The `_control_path`
attribute SHALL be initialized to `None`. Default values SHALL be
`user=None`, `port=22`, `key_path=None`.

#### Scenario: init stores all provided parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** no preconditions
- **When** `SSHTransport(host="myhost", user="ubuntu", port=2222, key_path="~/id_rsa")`
  is constructed
- **Then** `host` SHALL be `"myhost"`, `user` SHALL be `"ubuntu"`, `port` SHALL be `2222`,
  `key_path` SHALL be `str(Path("~/id_rsa").expanduser())`, and `_control_path` SHALL
  be `None`

#### Scenario: init uses defaults when optional params omitted

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** no preconditions
- **When** `SSHTransport(host="myhost")` is constructed
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`,
  and `_control_path` SHALL be `None`

### Requirement: SSHTransport target string

`_target()` SHALL return `"{user}@{host}"` when `user` is set, and just `host`
when `user` is `None`.

#### Scenario: target with user produces user@host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport(host="server", user="admin")`
- **When** `_target()` is called
- **Then** it SHALL return `"admin@server"`

#### Scenario: target without user produces host only

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport(host="server")`
- **When** `_target()` is called
- **Then** it SHALL return `"server"`

### Requirement: SSHTransport base SSH args

`_base_args()` SHALL return a list starting with `"ssh"`, including
`"StrictHostKeyChecking=no"` and the `ControlPath` option. When `port != 22`
it SHALL include `-p {port}`. When `key_path` is set it SHALL include
`-i {key_path}`.

#### Scenario: base args with default port and no key path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport(host="h")` with `_control_path="/tmp/sock"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"StrictHostKeyChecking=no"`,
  `"ControlPath=/tmp/sock"`, and SHALL NOT contain `"-p"` or `"-i"`

#### Scenario: base args with custom port and key path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport(host="h", port=2222, key_path="/home/u/.ssh/id_rsa")`
  with `_control_path="/tmp/sock"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"-p"`, `"2222"`, `"-i"`,
  and `"/home/u/.ssh/id_rsa"`

### Requirement: SSHTransport ensure control path

`_ensure_control()` SHALL create a control-path socket on first invocation via
`tempfile.mktemp` and establish an SSH control master by calling
`subprocess.run`. On subsequent invocations when `_control_path` is already set,
it SHALL be a no-op.

#### Scenario: ensure_control creates control path on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** `SSHTransport(host="h", user="u")` with `_control_path=None`,
  and `subprocess.run` and `tempfile.mktemp` are mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` SHALL be set to the mock temp path,
  and `subprocess.run` SHALL be called once with args containing
  `"ControlMaster=auto"`

#### Scenario: ensure_control is idempotent when path already set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** `SSHTransport(host="h")` with `_control_path="/tmp/existing"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` SHALL NOT be called

### Requirement: SSHTransport run_shell command composition

`run_shell()` SHALL prepend `cd '{cwd}' &&` to the command when `cwd` is
provided. It SHALL catch `subprocess.TimeoutExpired` and return
`{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`.
It SHALL catch any other exception and return
`{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: run_shell prepends cwd to command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` with `_control_path="/tmp/sock"`,
  and `subprocess.run` is mocked to succeed
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the last argument to `subprocess.run` SHALL be `"cd '/tmp' && ls"`

#### Scenario: run_shell handles timeout gracefully

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` with `_control_path="/tmp/sock"`,
  and `subprocess.run` is mocked to raise `TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result SHALL be
  `{"exit_code": -1, "stdout": "", "stderr": (containing "Timeout after 1s")}`

#### Scenario: run_shell handles generic exception gracefully

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` with `_control_path="/tmp/sock"`,
  and `subprocess.run` is mocked to raise `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result SHALL be
  `{"exit_code": -1, "stdout": "", "stderr": (containing "network error")}`

### Requirement: SSHTransport close

`close()` SHALL send `ssh -O exit` to tear down the control master and reset
`_control_path` to `None`. When `_control_path` is already `None`, `close()`
SHALL be a no-op.

#### Scenario: close sends exit signal and resets control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport(host="h", user="u")` with `_control_path="/tmp/sock"`,
  and `subprocess.run` is mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `"-O"` and `"exit"`,
  and `_control_path` SHALL be `None`

#### Scenario: close is noop without control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport(host="h")` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called
