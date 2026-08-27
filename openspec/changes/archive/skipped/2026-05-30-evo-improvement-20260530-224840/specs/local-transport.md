# local-transport.md

## ADDED Requirements

### Requirement: LocalTransport.run_shell delegates to subprocess.run

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with the provided `cmd`,
`cwd`, `timeout`, and `stdin_data`, and return a dict with keys `exit_code`,
`stdout`, `stderr` reflecting the completed-process result.

#### Scenario: successful command returns exit_code stdout stderr

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `returncode=0`, `stdout="ok"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result is `{"exit_code": 0, "stdout": "ok", "stderr": ""}`

#### Scenario: cwd parameter is forwarded to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the mocked `subprocess.run` is called with `cwd="/tmp"`

#### Scenario: timeout parameter is forwarded to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", timeout=30)` is called
- **Then** the mocked `subprocess.run` is called with `timeout=30`

#### Scenario: stdin_data is forwarded as input to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** the mocked `subprocess.run` is called with `input="hello"`

#### Scenario: default timeout is 120

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls")` is called without specifying timeout
- **Then** the mocked `subprocess.run` is called with `timeout=120`

#### Scenario: default cwd is None

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls")` is called without specifying cwd
- **Then** the mocked `subprocess.run` is called with `cwd=None`
