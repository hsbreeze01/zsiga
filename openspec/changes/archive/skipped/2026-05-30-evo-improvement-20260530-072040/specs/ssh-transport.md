# SSHTransport

## ADDED Requirements

### Requirement: SSHTransport initialization

`SSHTransport.__init__` SHALL accept `host`, `user`, `port`, and `key_path` parameters. It MUST store them as instance attributes. When `key_path` is provided, it SHALL be expanded via `Path.expanduser()` and converted to a string. `_control_path` MUST be initialized to `None`.

#### Scenario: SSHTransport stores all init parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with `host="server.com"`, `user="admin"`, `port=2222`, `key_path="~/.ssh/id_rsa"`
- **Then** `host` equals `"server.com"`, `user` equals `"admin"`, `port` equals `2222`, `key_path` equals the expanded path of `~/.ssh/id_rsa`, and `_control_path` is `None`

#### Scenario: SSHTransport uses default port 22 when not specified

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with only `host="server.com"`
- **Then** `port` equals `22`, `user` is `None`, `key_path` is `None`, `_control_path` is `None`

### Requirement: SSHTransport _target formatting

`SSHTransport._target` SHALL return `"{user}@{host}"` when `user` is set, or just `host` when `user` is `None`.

#### Scenario: _target with user returns user@host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="server.com"` and `user="admin"`
- **When** `_target()` is called
- **Then** the result is `"admin@server.com"`

#### Scenario: _target without user returns host only

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="server.com"` and `user=None`
- **When** `_target()` is called
- **Then** the result is `"server.com"`

### Requirement: SSHTransport _base_args composition

`SSHTransport._base_args` SHALL return a list starting with `["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ControlPath={control_path}"]`. When `port != 22`, it MUST include `["-p", str(port)]`. When `key_path` is set, it MUST include `["-i", key_path]`.

#### Scenario: _base_args includes strict host key checking and control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="server.com"`, `port=22`, `key_path=None`
- **When** `_base_args()` is called
- **Then** the result starts with `["ssh", "-o", "StrictHostKeyChecking=no"]`
- **And** the result contains `"-o"` and a string matching `ControlPath=`

#### Scenario: _base_args adds -p flag for non-default port

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222`
- **When** `_base_args()` is called
- **Then** the result contains `["-p", "2222"]`

#### Scenario: _base_args omits -p flag for default port 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=22`
- **When** `_base_args()` is called
- **Then** the result does NOT contain `"-p"`

#### Scenario: _base_args adds -i flag when key_path is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `key_path="/home/user/.ssh/id_rsa"`
- **When** `_base_args()` is called
- **Then** the result contains `["-i", "/home/user/.ssh/id_rsa"]`

### Requirement: SSHTransport _ensure_control idempotency

`SSHTransport._ensure_control` SHALL create a control path via `tempfile.mktemp` only once (when `_control_path` is `None`). If `_control_path` is already set, it MUST be a no-op. After creation, it SHALL establish the SSH control master by running `subprocess.run` with the base args plus control master options and the target.

#### Scenario: _ensure_control creates control path on first call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path=None` and `tempfile.mktemp` mocked to return `"/tmp/zsiga_ssh_abc"` and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` is set to `"/tmp/zsiga_ssh_abc"`
- **And** `subprocess.run` is called with args including `"ControlMaster=auto"` and the target

#### Scenario: _ensure_control is idempotent on second call

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path="/tmp/zsiga_ssh_existing"` and `subprocess.run` is mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called

### Requirement: SSHTransport run_shell with cwd prefix and error handling

`SSHTransport.run_shell` SHALL prefix the command with `cd '{cwd}' &&` when `cwd` is provided. It MUST call `_ensure_control()` before executing. On `subprocess.TimeoutExpired`, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`. On any other exception, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: run_shell prefixes cwd to command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_control_path` already set and `subprocess.run` mocked to return `returncode=0`, `stdout="done"`, `stderr=""`
- **When** `run_shell("make build", cwd="/home/user/project")` is called
- **Then** `subprocess.run` is called with args that end with `"cd '/home/user/project' && make build"`

#### Scenario: run_shell returns timeout dict on TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_control_path` already set and `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=60)` is called
- **Then** the return value is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 60s"}`

#### Scenario: run_shell returns error dict on generic OSError

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_control_path` already set and `subprocess.run` mocked to raise `OSError("connection refused")`
- **When** `run_shell("ls")` is called
- **Then** the return value is `{"exit_code": -1, "stdout": "", "stderr": "connection refused"}`

#### Scenario: run_shell without cwd passes command as-is

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_control_path` already set and `subprocess.run` mocked to return success
- **When** `run_shell("ls")` is called with no `cwd`
- **Then** `subprocess.run` is called with args that end with `"ls"` (no `cd` prefix)

### Requirement: SSHTransport close sends exit signal

`SSHTransport.close` SHALL send `ssh -O exit` to the target when `_control_path` is set. After sending, it MUST reset `_control_path` to `None`. If `_control_path` is `None`, `close()` MUST be a no-op.

#### Scenario: close sends exit signal and clears control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/zsiga_ssh_abc"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"`, `"exit"` and the target
- **And** `_control_path` is `None`

#### Scenario: close is a no-op when no control path exists

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run` is mocked
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called
