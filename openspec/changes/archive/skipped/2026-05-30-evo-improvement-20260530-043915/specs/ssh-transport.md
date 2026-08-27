# SSHTransport Test Coverage

## ADDED Requirements

### Requirement: SSHTransport initialization

`SSHTransport.__init__()` SHALL store `host`, `user`, `port`, `key_path` parameters. When `key_path` is provided it SHALL be expanded via `Path.expanduser()` and converted to string. The `_control_path` SHALL be initialized to `None`.

#### Scenario: SSHTransport stores init parameters

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with `host="myhost"`, `user="ubuntu"`, `port=2222`, `key_path="~/id_rsa"`
- **Then** `host` SHALL be `"myhost"`, `user` SHALL be `"ubuntu"`, `port` SHALL be `2222`, `key_path` SHALL be the expanded path string, and `_control_path` SHALL be `None`

#### Scenario: SSHTransport defaults user to None and port to 22

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** an `SSHTransport` constructed with only `host="myhost"`
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

### Requirement: SSHTransport._target property

`_target()` SHALL return `"{user}@{host}"` when `user` is set, or just `host` when `user` is `None`.

#### Scenario: _target with user

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="server"` and `user="admin"`
- **When** `_target()` is called
- **Then** the result SHALL be `"admin@server"`

#### Scenario: _target without user

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="server"` and `user=None`
- **When** `_target()` is called
- **Then** the result SHALL be `"server"`

### Requirement: SSHTransport._base_args SSH flag assembly

`_base_args()` SHALL return a list starting with `["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ControlPath={control_path}"]`. When `port` is not 22, it SHALL include `["-p", str(port)]`. When `key_path` is set, it SHALL include `["-i", key_path]`.

#### Scenario: _base_args default port and no key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=22`, `key_path=None`, and `_control_path="/tmp/sock"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"StrictHostKeyChecking=no"` and `"ControlPath=/tmp/sock"`, and SHALL NOT contain `-p` or `-i`

#### Scenario: _base_args with custom port and key

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=2222`, `key_path="/home/u/.ssh/id_rsa"`, and `_control_path="/tmp/sock"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `-p`, `2222`, `-i`, and the key path

### Requirement: SSHTransport._ensure_control establishes ControlMaster

`_ensure_control()` SHALL create a temporary control path via `tempfile.mktemp`, then call `subprocess.run` with SSH arguments including `ControlMaster=auto`, `ControlPath`, `ControlPersist=600`, and the target with `"true"`. It SHALL be idempotent — subsequent calls SHALL NOT create a new control path if one already exists.

#### Scenario: _ensure_control creates control path on first call

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run` and `tempfile.mktemp` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` SHALL be set to a non-None value, and `subprocess.run` SHALL be called once with args containing `"ControlMaster=auto"`

#### Scenario: _ensure_control is idempotent

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path` already set to `"/tmp/existing"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` SHALL NOT be called

### Requirement: SSHTransport.run_shell remote execution

`run_shell()` SHALL call `_ensure_control()`, prepend `cd '{cwd}' &&` to the command when `cwd` is provided, invoke SSH via `subprocess.run`, and return `{"exit_code", "stdout", "stderr"}`. On `subprocess.TimeoutExpired`, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`. On other exceptions, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: run_shell prepends cwd to command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked to no-op and `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` SHALL be called with args ending with `"cd '/tmp' && ls"`

#### Scenario: run_shell handles timeout

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked and `subprocess.run` raising `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result SHALL be `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}`

#### Scenario: run_shell handles generic exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked and `subprocess.run` raising `OSError("network error")`
- **When** `run_shell("ls")` is called
- **Then** the result SHALL be `{"exit_code": -1, "stdout": "", "stderr": "network error"}`

### Requirement: SSHTransport.close terminates ControlMaster

`close()` SHALL invoke `subprocess.run` with `ssh -O exit` to close the control master when `_control_path` is set, then set `_control_path` to `None`. When `_control_path` is already `None`, `close()` SHALL be a no-op.

#### Scenario: close sends exit signal when control path exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/sock"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `"-O"` and `"exit"`, and `_control_path` SHALL become `None`

#### Scenario: close is no-op without control path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called

