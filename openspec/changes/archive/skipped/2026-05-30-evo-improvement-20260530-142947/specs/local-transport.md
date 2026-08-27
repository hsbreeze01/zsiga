# spec: local-transport

## ADDED Requirements

### Requirement: LocalTransport delegates to subprocess.run

`LocalTransport` SHALL inherit from `Transport` and implement `run_shell` by calling `subprocess.run` with `shell=True`, `capture_output=True`, `text=True`, and forwarding `cwd`, `timeout`, and `stdin_data` (as `input`). The return value MUST be a dict with keys `exit_code` (int), `stdout` (str), and `stderr` (str).

#### Scenario: LocalTransport.run_shell returns parsed subprocess result

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `CompletedProcess(returncode=0, stdout="ok\n", stderr="")`
- **When** `run_shell("echo ok")` is called
- **Then** the result SHALL equal `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** the mock SHALL be called with `shell=True, cwd="/tmp", capture_output=True, text=True, timeout=30, input=None`

#### Scenario: LocalTransport.run_shell forwards stdin_data as input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** the mock SHALL be called with `input="hello"`

