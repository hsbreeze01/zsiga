# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport stores constructor parameters

`SSHTransport.__init__` SHALL store `host`, `user` (default `None`), `port` (default `22`), and `key_path` (default `None`, expanded via `Path.expanduser()`). The `_control_path` attribute SHALL be initialized to `None`.

#### Scenario: stores all parameters with defaults

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** a call `SSHTransport(host="myhost")`
- **When** the instance is created
- **Then** `host="myhost"`, `user=None`, `port=22`, `key_path=None`, `_control_path=None`

#### Scenario: stores custom parameters and expands key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** a call `SSHTransport(host="myhost", user="ubuntu", port=2222, key_path="~/id_rsa")`
- **When** the instance is created
- **Then** `key_path` equals `str(Path("~/id_rsa").expanduser())` and `port=2222`, `user="ubuntu"`

### Requirement: SSHTransport._target formats user@host

`_target()` SHALL return `"{user}@{host}"` when `user` is set, and just `host` when `user` is `None`.

#### Scenario: target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="server"`, `user="admin"`
- **When** `_target()` is called
- **Then** the result is `"admin@server"`

#### Scenario: target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="server"`, `user=None`
- **When** `_target()` is called
- **Then** the result is `"server"`

### Requirement: SSHTransport._base_args builds SSH argument list

`_base_args()` SHALL always include `"ssh"`, `"StrictHostKeyChecking=no"`, and `"ControlPath={control_path}"`. It SHALL include `-p {port}` only when `port != 22`. It SHALL include `-i {key_path}` only when `key_path` is set.

#### Scenario: default port and no key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with default port 22 and no key_path, with `_control_path="/tmp/sock"`
- **When** `_base_args()` is called
- **Then** the result contains `"StrictHostKeyChecking=no"` and `"ControlPath=/tmp/sock"` but NOT `-p` or `-i`

#### Scenario: custom port and key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222`, `key_path="/home/u/.ssh/id_rsa"`, `_control_path="/tmp/sock"`
- **When** `_base_args()` is called
- **Then** the result contains `-p`, `"2222"`, `-i`, and the key_path string

### Requirement: SSHTransport._ensure_control creates control master

`_ensure_control()` SHALL call `tempfile.mktemp` to create a control socket path, then call `subprocess.run` with SSH control master arguments. It SHALL be idempotent — if `_control_path` is already set, no subprocess call SHALL be made.

#### Scenario: creates control path on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path=None` and mocked `tempfile.mktemp` returning `"/tmp/zsiga_mock_sock"`
- **When** `_ensure_control()` is called
- **Then** `_control_path` is set to `"/tmp/zsiga_mock_sock"` and `subprocess.run` is called with `"ControlMaster=auto"` in args

#### Scenario: idempotent when control path already set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path="/tmp/existing"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called

### Requirement: SSHTransport.run_shell handles cwd, timeout, and errors

`run_shell()` SHALL prepend `cd '{cwd}' &&` to the command when `cwd` is provided. On `TimeoutExpired`, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`. On any other exception, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: prepends cwd to command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_control_path="/tmp/sock"` and a mocked `subprocess.run` returning success
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the last argument to `subprocess.run` is `"cd '/tmp' && ls"`

#### Scenario: handles timeout exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_control_path="/tmp/sock"` and a mocked `subprocess.run` raising `TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}`

#### Scenario: handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_control_path="/tmp/sock"` and a mocked `subprocess.run` raising `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result has `exit_code=-1`, `stdout=""`, and `"network error"` in `stderr`

### Requirement: SSHTransport.close cleans up control master

`close()` SHALL send an SSH control exit signal when `_control_path` is set, then reset `_control_path` to `None`. When `_control_path` is `None`, `close()` SHALL NOT call `subprocess.run`.

#### Scenario: sends exit signal and resets control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/sock"` and a mocked `subprocess.run`
- **When** `close()` is called
- **Then** `subprocess.run` is called with `-O exit` in args and `_control_path` becomes `None`

#### Scenario: noop without control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called
