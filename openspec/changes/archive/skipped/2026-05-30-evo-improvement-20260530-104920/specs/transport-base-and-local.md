# transport-base-and-local

## ADDED Requirements

### Requirement: Transport base class abstract contract

`Transport` SHALL serve as the abstract base class for all transport
implementations. Calling `run_shell()` on the base class MUST raise
`NotImplementedError`. The `close()` method on the base class SHALL be a
no-op (return `None` without error).

#### Scenario: base class run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a `Transport` instance
- **When** `run_shell("echo hello")` is called
- **Then** it MUST raise `NotImplementedError`

#### Scenario: base class close is no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close

- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` without raising any exception

---

### Requirement: LocalTransport delegates to subprocess.run

`LocalTransport` SHALL implement `run_shell()` by calling `subprocess.run`
with `shell=True`, `capture_output=True`, and `text=True`. It MUST return
a dictionary with exactly three keys: `"exit_code"` (int), `"stdout"` (str),
and `"stderr"` (str). The `cwd`, `timeout`, and `stdin_data` parameters SHALL
be forwarded to `subprocess.run` unchanged.

#### Scenario: run_shell returns structured dict from subprocess result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance with `subprocess.run` patched to return
  a mock with `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result MUST equal `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: run_shell forwards cwd to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance with `subprocess.run` patched
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` SHALL be called with `cwd="/tmp"`

#### Scenario: run_shell forwards timeout and stdin_data to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance with `subprocess.run` patched
- **When** `run_shell("cat", timeout=30, stdin_data="hello")` is called
- **Then** `subprocess.run` SHALL be called with `timeout=30` and
  `input="hello"`

#### Scenario: LocalTransport close is no-op

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.close

- **Given** a `LocalTransport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` without raising any exception
