# local-transport

## ADDED Requirements

### Requirement: LocalTransport.run_shell SHALL delegate to subprocess.run

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with the given
command string (`shell=True`), forward `cwd`, `timeout`, and `stdin_data`
parameters, and return a dict with keys `exit_code`, `stdout`, `stderr`.

#### Scenario: successful command returns exit_code stdout stderr dict

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  a `CompletedProcess` with `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result SHALL be `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`
- **And** `subprocess.run` SHALL have been called with `shell=True`

#### Scenario: cwd and timeout and stdin_data are forwarded to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", cwd="/tmp", timeout=30, stdin_data="hello")` is called
- **Then** `subprocess.run` SHALL have been called with `cwd="/tmp"`,
  `timeout=30`, `input="hello"`

#### Scenario: subprocess TimeoutExpired is propagated

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to raise
  `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** `subprocess.TimeoutExpired` SHALL be raised
