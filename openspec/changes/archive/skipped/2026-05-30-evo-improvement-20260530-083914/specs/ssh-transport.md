# Spec: SSHTransport

## ADDED Requirements

### Requirement: SSHTransport Constructor Stores Parameters

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, `key_path` as instance attributes. `key_path` SHALL be expanded via `Path.expanduser()` and converted to `str`. `_control_path` SHALL be initialized to `None`.

#### Scenario: SSHTransport stores host user port key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport("myhost", user="ubuntu", port=2222, key_path="~/.ssh/id_rsa")` is constructed
- **When** attributes are inspected
- **Then** `host` is `"myhost"`, `user` is `"ubuntu"`, `port` is `2222`, `key_path` is the expanded absolute path of `~/.ssh/id_rsa`, and `_control_path` is `None`

#### Scenario: SSHTransport defaults user to None and port to 22

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** `SSHTransport("myhost")` is constructed
- **When** attributes are inspected
- **Then** `user` is `None`, `port` is `22`, `key_path` is `None`

---

### Requirement: SSHTransport._target Formats Target String

`_target()` SHALL return `"{user}@{host}"` when `user` is set, otherwise just `host`.

#### Scenario: _target returns user@host when user is set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport("host1", user="root")`
- **When** `_target()` is called
- **Then** the result is `"root@host1"`

#### Scenario: _target returns host when user is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target

- **Given** `SSHTransport("host1")`
- **When** `_target()` is called
- **Then** the result is `"host1"`

---

### Requirement: SSHTransport._base_args Builds SSH Argument List

`_base_args()` SHALL return a list starting with `"ssh"` and containing `-o StrictHostKeyChecking=no` and a `ControlPath` option. When `port` is not 22, it SHALL include `-p {port}`. When `key_path` is set, it SHALL include `-i {key_path}`.

#### Scenario: _base_args includes port flag when port is not 22

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport("host1", port=2222)` with `_control_path` set to `"/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"` and `"2222"`

#### Scenario: _base_args includes identity flag when key_path is set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport("host1", key_path="/home/user/.ssh/id_rsa")` with `_control_path` set to `"/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result contains `"-i"` and `"/home/user/.ssh/id_rsa"`

#### Scenario: _base_args omits port flag when port is 22

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args

- **Given** `SSHTransport("host1", port=22)` with `_control_path` set to `"/tmp/ctrl"`
- **When** `_base_args()` is called
- **Then** the result does not contain `"-p"`

---

### Requirement: SSHTransport._ensure_control Is Idempotent

`_ensure_control()` SHALL call `subprocess.run` exactly once to establish the SSH control master. Subsequent calls SHALL NOT invoke `subprocess.run` again. After the first call, `_control_path` SHALL be a non-None string.

#### Scenario: _ensure_control calls subprocess.run once and sets control_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** `SSHTransport("host1")` with `_control_path` initially `None`, and `subprocess.run` is mocked
- **When** `_ensure_control()` is called once
- **Then** `subprocess.run` is called exactly once, and `_control_path` is a non-None string starting with `"zsiga_ssh_"`

#### Scenario: _ensure_control is idempotent on second call

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** `SSHTransport("host1")` with `_control_path` initially `None`, and `subprocess.run` is mocked
- **When** `_ensure_control()` is called twice
- **Then** `subprocess.run` is called exactly once

---

### Requirement: SSHTransport.run_shell Prepends cd and Handles Timeout

`run_shell()` SHALL first call `_ensure_control()`, then build an SSH command. When `cwd` is provided, the remote command SHALL be prefixed with `cd '{cwd}' &&`. On `subprocess.TimeoutExpired`, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after {timeout}s"}`. On other exceptions, it SHALL return `{"exit_code": -1, "stdout": "", "stderr": str(e)}`.

#### Scenario: run_shell prefixes cd when cwd is given

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport("host1")` with `_control_path` set to `"/tmp/ctrl"`, and `subprocess.run` is mocked to return a `CompletedProcess(returncode=0, stdout="out", stderr="")`
- **When** `run_shell("ls", cwd="/var")` is called
- **Then** `subprocess.run` is called with args that contain `"cd '/var' && ls"`

#### Scenario: run_shell does not prefix cd when cwd is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport("host1")` with `_control_path` set to `"/tmp/ctrl"`, and `subprocess.run` is mocked to return a `CompletedProcess(returncode=0, stdout="out", stderr="")`
- **When** `run_shell("ls")` is called
- **Then** `subprocess.run` is called with args that contain `"ls"` but NOT `"cd"`

#### Scenario: run_shell returns exit_code -1 on TimeoutExpired

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport("host1")` with `_control_path` set to `"/tmp/ctrl"`, and `subprocess.run` is mocked to raise `subprocess.TimeoutExpired(cmd="ssh", timeout=120)`
- **When** `run_shell("sleep 999", timeout=120)` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 120s"}`

#### Scenario: run_shell returns exit_code -1 on generic exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** `SSHTransport("host1")` with `_control_path` set to `"/tmp/ctrl"`, and `subprocess.run` is mocked to raise `OSError("connection lost")`
- **When** `run_shell("ls")` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": "connection lost"}`

---

### Requirement: SSHTransport.close Sends Control Exit

`close()` SHALL send `ssh -O exit` to tear down the control master when `_control_path` is set. If `_control_path` is `None`, `close()` SHALL be a no-op.

#### Scenario: close sends -O exit when control_path is set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport("host1")` with `_control_path` set to `"/tmp/ctrl"`, and `subprocess.run` is mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"` and `"exit"`, and `_control_path` is set to `None`

#### Scenario: close is no-op when control_path is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** `SSHTransport("host1")` with `_control_path` as `None`, and `subprocess.run` is mocked
- **When** `close()` is called
- **Then** `subprocess.run` is NOT called

