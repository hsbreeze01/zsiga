# SSHTransport Unit Tests

## ADDED Requirements

### Requirement: SSHTransport constructor stores parameters

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and `key_path` as
instance attributes. `key_path` SHALL be expanded via `Path.expanduser()` and
converted to `str`. `_control_path` SHALL be initialized to `None`.

#### Scenario: SSHTransport stores all constructor params

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="myhost", user="alice", port=2222, key_path="~/.ssh/id_rsa")` is constructed
- **Then** `host=="myhost"`, `user=="alice"`, `port==2222`, `key_path` is the expanded path string, and `_control_path is None`

#### Scenario: SSHTransport defaults for optional params

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="myhost")` is constructed
- **Then** `user is None`, `port==22`, `key_path is None`, `_control_path is None`

### Requirement: SSHTransport._target builds user@host string

`_target()` SHALL return `"{user}@{host}"` when `user` is set, otherwise just `host`.

#### Scenario: _target with user returns user@host

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** `SSHTransport(host="server", user="bob")`
- **When** `_target()` is called
- **Then** result is `"bob@server"`

#### Scenario: _target without user returns host only

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** `SSHTransport(host="server")`
- **When** `_target()` is called
- **Then** result is `"server"`

### Requirement: SSHTransport._base_args assembles SSH arguments

`_base_args()` SHALL return a list starting with `["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ControlPath=..."]`.
When `port != 22`, it SHALL include `["-p", str(port)]`.
When `key_path` is set, it SHALL include `["-i", key_path]`.

#### Scenario: _base_args includes port when non-default

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** `SSHTransport(host="h", port=2222)` with `_control_path` set to `"/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"` and `"2222"`

#### Scenario: _base_args omits port when default 22

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** `SSHTransport(host="h", port=22)` with `_control_path` set to `"/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result does NOT contain `"-p"`

#### Scenario: _base_args includes key_path when set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** `SSHTransport(host="h", key_path="/home/user/.ssh/key")` with `_control_path` set to `"/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result contains `"-i"` and `"/home/user/.ssh/key"`

### Requirement: SSHTransport._ensure_control is idempotent

`_ensure_control()` SHALL create a control path via `tempfile.mktemp` and call
`subprocess.run` to establish the SSH control master only on the first invocation.
Subsequent calls SHALL be no-ops when `_control_path` is already set.

#### Scenario: _ensure_control skips when control_path already set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** `SSHTransport(host="h")` with `_control_path` pre-set to `"/tmp/existing"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called and `_control_path` remains `"/tmp/existing"`

### Requirement: SSHTransport.run_shell handles timeouts and errors

`run_shell()` SHALL catch `subprocess.TimeoutExpired` and return
`{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`.
It SHALL catch any other `Exception` and return `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.
When `cwd` is provided, it SHALL prefix the command with `cd '{cwd}' &&`.

#### Scenario: SSHTransport.run_shell returns timeout dict on TimeoutExpired

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** `SSHTransport(host="h")` with `_control_path` set, and `subprocess.run` mocked to raise `TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** result is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}`

#### Scenario: SSHTransport.run_shell returns error dict on generic Exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** `SSHTransport(host="h")` with `_control_path` set, and `subprocess.run` mocked to raise `OSError("Network unreachable")`
- **When** `run_shell("ls")` is called
- **Then** result is `{"exit_code": -1, "stdout": "", "stderr": "Network unreachable"}`

#### Scenario: SSHTransport.run_shell prefixes cwd to command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** `SSHTransport(host="h")` with `_control_path` set, and `subprocess.run` mocked to return a successful result
- **When** `run_shell("ls", cwd="/var/log")` is called
- **Then** `subprocess.run` is called with args ending in `"cd '/var/log' && ls"`

### Requirement: SSHTransport.close tears down control master

`close()` SHALL invoke `ssh -O exit` with the control path and reset `_control_path` to `None`.
If `_control_path` is `None` (or falsy), `close()` SHALL be a no-op.

#### Scenario: SSHTransport.close sends ssh -O exit and resets control_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** `SSHTransport(host="h")` with `_control_path` set to `"/tmp/ctrl"`, and `subprocess.run` is mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"` and `"exit"`, and `_control_path is None`

#### Scenario: SSHTransport.close is no-op when no control path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** `SSHTransport(host="h")` with `_control_path is None`
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called

