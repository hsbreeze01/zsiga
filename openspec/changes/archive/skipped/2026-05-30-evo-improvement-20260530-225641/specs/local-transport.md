# local-transport

## ADDED Requirements

### Requirement: LocalTransport.run_shell subprocess invocation

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with `shell=True`,
`capture_output=True`, `text=True`, and forward `cwd`, `timeout`, and
`stdin_data`.  It MUST return a dict with keys `exit_code`, `stdout`, `stderr`
mirroring the `subprocess.CompletedProcess` result.

#### Scenario: LocalTransport.run_shell returns structured result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `CompletedProcess(returncode=0, stdout="ok\n", stderr="")`
- **When** `run_shell("echo ok")` is called
- **Then** the result SHALL equal `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards all parameters

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30, stdin_data="hello")` is called
- **Then** `subprocess.run` SHALL be called with `shell=True`, `cwd="/tmp"`,
  `timeout=30`, `input="hello"`, `capture_output=True`, `text=True`

#### Scenario: LocalTransport.run_shell propagates non-zero exit code

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `CompletedProcess(returncode=1, stdout="", stderr="error")`
- **When** `run_shell("false")` is called
- **Then** the result SHALL equal `{"exit_code": 1, "stdout": "", "stderr": "error"}`
