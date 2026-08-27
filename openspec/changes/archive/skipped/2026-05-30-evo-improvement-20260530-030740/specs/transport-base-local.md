# transport-base-local

## ADDED Requirements

### Requirement: Transport ABC Contract
The `Transport` base class SHALL define `run_shell()` and `close()` as part of its
public interface. Calling `run_shell()` on the base class directly MUST raise
`NotImplementedError`. Calling `close()` on the base class MUST complete without
error (no-op).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` base class instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close is a safe no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` base class instance
- **When** `close()` is called
- **Then** no exception is raised and the call returns `None`

### Requirement: LocalTransport Subprocess Delegation
`LocalTransport.run_shell()` SHALL delegate to `subprocess.run` with `shell=True`,
`capture_output=True`, `text=True`, and forward `cwd`, `timeout`, and `input`
(`stdin_data`) parameters. The return value MUST be a dict with keys
`exit_code` (int), `stdout` (str), and `stderr` (str).

#### Scenario: LocalTransport.run_shell returns structured result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return
  `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result dict is `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd parameter

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"`

#### Scenario: LocalTransport.run_shell forwards timeout parameter

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("sleep 1", timeout=5)` is called
- **Then** `subprocess.run` is called with `timeout=5`

#### Scenario: LocalTransport.run_shell forwards stdin_data parameter

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`
