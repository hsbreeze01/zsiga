# local-transport.md

## ADDED Requirements

### Requirement: Transport Abstract Base Class

The `Transport` base class SHALL define the interface contract for all transport
implementations. `run_shell` MUST raise `NotImplementedError` when called on the
base class. `close` SHALL be a no-op on the base class.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** it MUST raise `NotImplementedError`

#### Scenario: Transport.close does not raise

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception SHALL be raised

### Requirement: LocalTransport Command Execution

`LocalTransport` SHALL execute shell commands locally via `subprocess.run` with
`shell=True` and return a dict containing `exit_code`, `stdout`, and `stderr`.

#### Scenario: LocalTransport.run_shell returns result dict on success

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result MUST be `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell returns non-zero exit code

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `returncode=1`, `stdout=""`, `stderr="error"`
- **When** `run_shell("false")` is called
- **Then** the result MUST contain `exit_code=1` and `stderr="error"`

#### Scenario: LocalTransport.run_shell forwards cwd to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` MUST be called with `cwd="/tmp"`

#### Scenario: LocalTransport.run_shell forwards timeout to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("sleep 1", timeout=5)` is called
- **Then** `subprocess.run` MUST be called with `timeout=5`

#### Scenario: LocalTransport.run_shell forwards stdin_data to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` MUST be called with `input="hello"`

#### Scenario: LocalTransport.run_shell uses shell=True

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("echo hi")` is called
- **Then** `subprocess.run` MUST be called with `shell=True`
