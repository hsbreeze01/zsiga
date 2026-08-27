# local-transport

## ADDED Requirements

### Requirement: LocalTransport wraps subprocess.run

`LocalTransport.run_shell` SHALL execute commands locally via `subprocess.run`
with `shell=True`, `capture_output=True`, and `text=True`. It MUST return a
dict with keys `exit_code` (int), `stdout` (str), and `stderr` (str).

#### Scenario: run_shell returns structured result from subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return
  `returncode=0`, `stdout="hello\n"`, `stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result is `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

#### Scenario: run_shell forwards cwd to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"`

#### Scenario: run_shell forwards stdin_data to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

#### Scenario: run_shell forwards timeout to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("sleep 5", timeout=30)` is called
- **Then** `subprocess.run` is called with `timeout=30`

#### Scenario: run_shell calls subprocess with shell=True

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked
- **When** `run_shell("echo hi")` is called
- **Then** `subprocess.run` is called with `shell=True` and `capture_output=True`
      and `text=True`

#### Scenario: LocalTransport.close is a no-op

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.close
- **Given** a `LocalTransport` instance
- **When** `close()` is called
- **Then** no exception is raised
