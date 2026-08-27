# Spec: Transport Base Class and LocalTransport

## ADDED Requirements

### Requirement: Transport is an abstract base class with run_shell and close

`Transport` SHALL define `run_shell(cmd, cwd, timeout, stdin_data)` and `close()` methods.
`run_shell` on the base class MUST raise `NotImplementedError`.
`close` on the base class SHALL be a no-op (pass).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close is a no-op

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the method returns `None`

### Requirement: LocalTransport.run_shell executes via subprocess

`LocalTransport` SHALL execute the given shell command via `subprocess.run` and return a dict with keys `exit_code` (int), `stdout` (str), and `stderr` (str).

#### Scenario: LocalTransport.run_shell returns subprocess output on success

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `returncode=0`, `stdout="hello\n"`, `stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result dict SHALL equal `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell returns non-zero exit_code on failure

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `returncode=1`, `stdout=""`, `stderr="error msg"`
- **When** `run_shell("false")` is called
- **Then** the result dict SHALL equal `{"exit_code": 1, "stdout": "", "stderr": "error msg"}`

