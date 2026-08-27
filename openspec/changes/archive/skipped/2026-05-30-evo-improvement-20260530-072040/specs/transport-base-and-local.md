# Transport Base Class and LocalTransport

## ADDED Requirements

### Requirement: Transport base class contract

`Transport` SHALL define `run_shell(cmd, cwd, timeout, stdin_data)` and `close()` as abstract interface methods. Calling `run_shell` on the base class MUST raise `NotImplementedError`. Calling `close()` on the base class MUST be a no-op (return `None`).

#### Scenario: run_shell raises NotImplementedError on base Transport

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hello")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: close is a no-op on base Transport

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the return value is `None`

### Requirement: LocalTransport delegates to subprocess.run

`LocalTransport.run_shell` SHALL invoke `subprocess.run` with `shell=True`, `capture_output=True`, `text=True`, and forward `cwd`, `timeout`, and `stdin_data` (via `input`). It MUST return a dict with keys `exit_code` (int), `stdout` (str), and `stderr` (str) extracted from the `CompletedProcess` result.

#### Scenario: LocalTransport.run_shell forwards all parameters to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return a `CompletedProcess` with `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("ls -la", cwd="/tmp", timeout=30, stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `cmd="ls -la"`, `shell=True`, `cwd="/tmp"`, `capture_output=True`, `text=True`, `timeout=30`, `input="hello"`
- **And** the return value equals `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell with defaults uses timeout=120

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("echo hi")` is called with no optional arguments
- **Then** `subprocess.run` is called with `timeout=120`, `cwd=None`, `input=None`
