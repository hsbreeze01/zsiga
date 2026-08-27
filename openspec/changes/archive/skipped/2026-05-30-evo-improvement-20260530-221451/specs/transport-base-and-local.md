# transport-base-and-local

## ADDED Requirements

### Requirement: Transport base class contract

The `Transport` base class SHALL define the interface contract for all transport
implementations.

#### Scenario: run_shell raises NotImplementedError on base class

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** it SHALL raise `NotImplementedError`

#### Scenario: close is a no-op on base class

- **testable**: true
- **target**: zsiga/transport.py::Transport.close

- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** it SHALL return `None` without raising any exception

### Requirement: LocalTransport run_shell return value

`LocalTransport.run_shell()` SHALL invoke `subprocess.run` with `shell=True`,
`capture_output=True`, and `text=True`, and return a dict with keys
`exit_code`, `stdout`, `stderr` derived from the `CompletedProcess` result.

#### Scenario: run_shell returns dict with exit_code, stdout, stderr

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `returncode=0, stdout="hello\n", stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result SHALL equal `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

### Requirement: LocalTransport forwards subprocess kwargs

`LocalTransport.run_shell()` SHALL forward its `cwd`, `timeout`, and `stdin_data`
keyword arguments to `subprocess.run` under the corresponding parameter names
(`cwd`, `timeout`, `input`). It SHALL also always pass `shell=True`,
`capture_output=True`, `text=True`.

#### Scenario: run_shell forwards cwd to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` SHALL be called with `cwd="/tmp"`

#### Scenario: run_shell forwards timeout to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", timeout=30)` is called
- **Then** `subprocess.run` SHALL be called with `timeout=30`

#### Scenario: run_shell forwards stdin_data as input to subprocess.run

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` SHALL be called with `input="hello"`

#### Scenario: run_shell uses shell=True and captures output as text

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("echo hi")` is called
- **Then** `subprocess.run` SHALL be called with `shell=True`, `capture_output=True`,
  and `text=True`
