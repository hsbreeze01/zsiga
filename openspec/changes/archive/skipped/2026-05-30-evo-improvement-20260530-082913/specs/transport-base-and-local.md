# transport-base-and-local

## ADDED Requirements

### REQ-TBL-001: Transport base class interface

`Transport` SHALL define an abstract interface for shell execution and resource cleanup.

- `run_shell` SHALL raise `NotImplementedError` when called directly.
- `close` SHALL return `None` and complete without error.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` base instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close returns None

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` base instance
- **When** `close()` is called
- **Then** the return value is `None`

### REQ-TBL-002: LocalTransport subprocess delegation

`LocalTransport` SHALL delegate shell execution to `subprocess.run` with `shell=True`, `capture_output=True`, `text=True`, and return a structured dict containing `exit_code`, `stdout`, and `stderr`.

#### Scenario: LocalTransport.run_shell returns structured result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return `returncode=0`, `stdout="hello\n"`, `stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result equals `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell passes cwd to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"`

#### Scenario: LocalTransport.run_shell passes stdin_data as input

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

#### Scenario: LocalTransport.run_shell respects timeout parameter

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("sleep 5", timeout=30)` is called
- **Then** `subprocess.run` is called with `timeout=30`
