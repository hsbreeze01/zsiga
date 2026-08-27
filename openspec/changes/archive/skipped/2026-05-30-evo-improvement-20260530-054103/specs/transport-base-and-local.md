# Transport Base Class & LocalTransport

## ADDED Requirements

### Requirement: Transport base class raises NotImplementedError for run_shell

`Transport` is an abstract base class. Calling `run_shell` on it SHALL raise
`NotImplementedError`.

#### Scenario: calling run_shell on Transport base raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a `Transport` instance
- **When** `run_shell("echo hello")` is called
- **Then** `NotImplementedError` is raised

### Requirement: Transport base class close is a no-op

`Transport.close()` SHALL return `None` without raising.

#### Scenario: calling close on Transport base does not raise

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close

- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the return value is `None`

### Requirement: LocalTransport.run_shell delegates to subprocess.run

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with the provided
`cmd`, `cwd`, `timeout`, and `stdin_data` arguments, and return a dict with
keys `exit_code`, `stdout`, `stderr`.

#### Scenario: LocalTransport.run_shell returns subprocess result dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result dict equals `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell passes cwd and timeout to subprocess

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"` and `timeout=30`

#### Scenario: LocalTransport.run_shell passes stdin_data as input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

