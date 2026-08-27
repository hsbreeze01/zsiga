# transport-base-and-local

## ADDED Requirements

### Requirement: Transport base class is abstract

The `Transport` base class SHALL raise `NotImplementedError` when `run_shell` is called directly. The `close` method SHALL be a no-op that returns `None`.

#### Scenario: run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: close returns None without error

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** the result is `None` and no exception is raised

### Requirement: LocalTransport delegates to subprocess.run

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with `shell=True`, `capture_output=True`, `text=True` and SHALL return a dict with keys `exit_code`, `stdout`, `stderr` extracted from the completed process. It SHALL forward `cwd`, `timeout`, and `stdin_data` (as `input`) to `subprocess.run`.

#### Scenario: run_shell returns structured dict

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and a mocked `subprocess.run` that returns `returncode=0, stdout="hello\n", stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result equals `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

#### Scenario: run_shell forwards cwd parameter

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and a mocked `subprocess.run`
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"`

#### Scenario: run_shell forwards timeout parameter

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and a mocked `subprocess.run`
- **When** `run_shell("ls", timeout=30)` is called
- **Then** `subprocess.run` is called with `timeout=30`

#### Scenario: run_shell forwards stdin_data as input

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and a mocked `subprocess.run`
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

#### Scenario: run_shell uses shell=True and captures output

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and a mocked `subprocess.run`
- **When** `run_shell("echo hi")` is called
- **Then** `subprocess.run` is called with `shell=True`, `capture_output=True`, `text=True`
