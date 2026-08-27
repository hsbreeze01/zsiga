# transport-base-and-local

## ADDED Requirements

### REQ-TBL-001: Transport base class run_shell SHALL raise NotImplementedError

Transport is an abstract base class. Calling `run_shell` on it directly
MUST signal that the subclass has not provided an implementation.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a `Transport` instance (base class, not subclass)
- **When** `run_shell("echo hi")` is called
- **Then** it SHALL raise `NotImplementedError`

---

### REQ-TBL-002: Transport base class close SHALL be a no-op

The base `close` method provides a safe default so callers can always
invoke `close()` without checking the transport type.

#### Scenario: Transport.close returns without error

- **testable**: true
- **target**: zsiga/transport.py::Transport.close

- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` and raise no exception

---

### REQ-TBL-003: LocalTransport.run_shell SHALL delegate to subprocess and return structured dict

`LocalTransport` wraps `subprocess.run` and returns a normalized dict
with keys `exit_code`, `stdout`, `stderr`.

#### Scenario: LocalTransport.run_shell returns structured result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `returncode=0, stdout="ok", stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result SHALL equal `{"exit_code": 0, "stdout": "ok", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` SHALL be called with `cwd="/tmp"` and `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` SHALL be called with `input="hello"`

---

### REQ-TBL-004: LocalTransport.close SHALL be a no-op

Closing a local transport requires no cleanup.

#### Scenario: LocalTransport.close returns without error

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.close

- **Given** a `LocalTransport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` and raise no exception
