# SSHTransport Behavior

## ADDED Requirements

### Requirement: SSHTransport.__init__ stores connection parameters

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, `key_path` (with
`Path.expanduser()` applied) and initialize `_control_path` to `None`.

#### Scenario: constructor sets all attributes from arguments

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** no preconditions
- **When** `SSHTransport(host="srv", user="alice", port=2222, key_path="~/.ssh/id")` is constructed
- **Then** `host` is `"srv"`, `user` is `"alice"`, `port` is `2222`,
  `key_path` is the expanded form of `~/.ssh/id`, and `_control_path` is `None`

#### Scenario: constructor uses defaults for user, port, key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** no preconditions
- **When** `SSHTransport(host="srv")` is constructed
- **Then** `user` is `None`, `port` is `22`, `key_path` is `None`

### Requirement: SSHTransport._target formats user@host or host-only string

`_target()` SHALL return `"{user}@{host}"` when `user` is set, otherwise just
`host`.

#### Scenario: _target with user returns user@host

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport(host="srv", user="alice")`
- **When** `_target()` is called
- **Then** the result is `"alice@srv"`

#### Scenario: _target without user returns host only

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport(host="srv")`
- **When** `_target()` is called
- **Then** the result is `"srv"`

### Requirement: SSHTransport._base_args assembles SSH arguments

`_base_args()` SHALL return a list starting with `"ssh"` and including
`StrictHostKeyChecking=no`, `ControlPath`, optional port (`-p`), and optional
identity file (`-i`).

#### Scenario: _base_args with default port and no key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport(host="srv")`
- **When** `_base_args()` is called
- **Then** the list contains `"ssh"`, `"-o"`, `"StrictHostKeyChecking=no"` but does NOT contain `"-p"` or `"-i"`

#### Scenario: _base_args with custom port and key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport(host="srv", port=2222, key_path="/key")`
- **When** `_base_args()` is called
- **Then** the list contains `"-p"`, `"2222"`, `"-i"`, `"/key"`

### Requirement: SSHTransport._ensure_control establishes ControlMaster

`_ensure_control()` SHALL create a temp control path and run SSH with
`ControlMaster=auto` if `_control_path` is `None`. It SHALL be a no-op when
`_control_path` is already set.

#### Scenario: _ensure_control skips when control_path already set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** `SSHTransport(host="srv")` with `_control_path` pre-set to `"/tmp/ctrl"`
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called and `_control_path` remains `"/tmp/ctrl"`

### Requirement: SSHTransport.run_shell prepends cd when cwd is provided

When `cwd` is given, `run_shell` SHALL prepend `cd '<cwd>' &&` to the remote
command.

#### Scenario: run_shell with cwd prepends cd command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport(host="srv")` with `_ensure_control` mocked to no-op
  and `subprocess.run` mocked to return `returncode=0, stdout="", stderr=""`
- **When** `run_shell("ls", cwd="/home/alice")` is called
- **Then** the SSH args passed to `subprocess.run` include `"cd '/home/alice' && ls"`

#### Scenario: run_shell without cwd does not prepend cd

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport(host="srv")` with `_ensure_control` mocked to no-op
  and `subprocess.run` mocked to return `returncode=0, stdout="", stderr=""`
- **When** `run_shell("ls")` is called
- **Then** the last argument in the SSH args is `"ls"`

### Requirement: SSHTransport.run_shell handles subprocess.TimeoutExpired

When `subprocess.run` raises `TimeoutExpired`, `run_shell` SHALL return a dict
with `exit_code=-1` and `stderr` containing `"Timeout"`.

#### Scenario: run_shell returns timeout result on TimeoutExpired

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport(host="srv")` with `_ensure_control` mocked to no-op
  and `subprocess.run` mocked to raise `subprocess.TimeoutExpired("ssh", 120)`
- **When** `run_shell("sleep 999")` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 120s"}`

### Requirement: SSHTransport.run_shell handles generic exceptions

When `subprocess.run` raises a generic `Exception`, `run_shell` SHALL return a
dict with `exit_code=-1` and `stderr` containing the exception message.

#### Scenario: run_shell returns error result on generic exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport(host="srv")` with `_ensure_control` mocked to no-op
  and `subprocess.run` mocked to raise `RuntimeError("connection lost")`
- **When** `run_shell("ls")` is called
- **Then** `result["exit_code"]` is `-1` and `"connection lost"` is in `result["stderr"]`

### Requirement: SSHTransport.close terminates the ControlMaster

`close()` SHALL invoke `ssh -O exit` via `subprocess.run` when `_control_path`
is set, then reset `_control_path` to `None`. It SHALL be a no-op when
`_control_path` is `None`.

#### Scenario: close sends exit signal and resets control_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport(host="srv")` with `_control_path` set to `"/tmp/ctrl"`
  and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"`, `"exit"` and
  `_control_path` is `None`

#### Scenario: close is no-op when control_path is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport(host="srv")` with `_control_path` set to `None`
  and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called

