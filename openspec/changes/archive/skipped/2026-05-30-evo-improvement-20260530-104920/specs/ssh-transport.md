# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport initialisation stores connection parameters

`SSHTransport.__init__` SHALL accept `host` (required), `user` (optional),
`port` (default 22), and `key_path` (optional). When `key_path` is provided,
it MUST be expanded via `Path.expanduser()` and stored as a string. The
`_control_path` attribute SHALL initially be `None`.

#### Scenario: init stores host user port key_path with expanduser

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** key_path `"~/id_rsa"` exists in the user's home directory
- **When** `SSHTransport(host="srv", user="alice", port=2222, key_path="~/id_rsa")`
  is constructed
- **Then** `.host` SHALL be `"srv"`, `.user` SHALL be `"alice"`,
  `.port` SHALL be `2222`, `.key_path` SHALL be the expanded absolute path,
  and `._control_path` SHALL be `None`

#### Scenario: init with minimal arguments uses defaults

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__

- **Given** no optional arguments
- **When** `SSHTransport(host="srv")` is constructed
- **Then** `.user` SHALL be `None`, `.port` SHALL be `22`,
  `.key_path` SHALL be `None`, and `._control_path` SHALL be `None`

---

### Requirement: SSHTransport run_shell executes via SSH

`SSHTransport.run_shell()` SHALL establish a control master connection on
first call (via `_ensure_control`), then execute commands through SSH. It
MUST return the standard `{"exit_code", "stdout", "stderr"}` dictionary.
When `cwd` is provided, the remote command SHALL be prefixed with
`cd '<cwd>' &&`. When `subprocess.TimeoutExpired` is raised, it MUST return
`exit_code=-1`. For any other exception, it MUST also return `exit_code=-1`
with the exception message in `stderr`.

#### Scenario: run_shell returns structured dict via SSH

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` instance with `subprocess.run` patched to return
  `returncode=0`, `stdout="out"`, `stderr="err"`
- **When** `run_shell("whoami")` is called
- **Then** the result MUST equal `{"exit_code": 0, "stdout": "out", "stderr": "err"}`

#### Scenario: run_shell with cwd prepends cd command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` instance with `subprocess.run` patched
- **When** `run_shell("ls", cwd="/var/log")` is called
- **Then** the SSH command arguments SHALL contain `"cd '/var/log' && ls"`

#### Scenario: run_shell timeout returns exit_code minus one

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` instance with `subprocess.run` patched to raise
  `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the result `exit_code` SHALL be `-1`, `stdout` SHALL be `""`,
  and `stderr` SHALL contain `"Timeout"`

#### Scenario: run_shell generic exception returns exit_code minus one

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell

- **Given** an `SSHTransport` instance with `subprocess.run` patched to raise
  `OSError("connection lost")`
- **When** `run_shell("cmd")` is called
- **Then** the result `exit_code` SHALL be `-1` and `stderr` SHALL contain
  `"connection lost"`

---

### Requirement: SSHTransport close terminates control master

`SSHTransport.close()` SHALL, when a control path is active, execute
`ssh -O exit` to terminate the SSH ControlMaster and reset `_control_path`
to `None`. If no control path is active, close SHALL be a no-op.

#### Scenario: close with active control path sends exit command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** an `SSHTransport` instance with `_control_path` set to a non-None
  value and `subprocess.run` patched
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with arguments containing
  `"-O"` and `"exit"`, and `_control_path` SHALL be `None` after the call

#### Scenario: close without active control path is no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close

- **Given** an `SSHTransport` instance with `_control_path` set to `None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called
