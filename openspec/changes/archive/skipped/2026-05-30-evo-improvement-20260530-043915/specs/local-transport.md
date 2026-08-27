# LocalTransport Test Coverage

## ADDED Requirements

### Requirement: LocalTransport.run_shell delegates to subprocess.run

`LocalTransport.run_shell()` SHALL invoke `subprocess.run` with the given command string in shell mode, capturing stdout and stderr as text, and return a dict with keys `exit_code`, `stdout`, `stderr` matching the subprocess result.

#### Scenario: LocalTransport.run_shell returns subprocess result

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return `returncode=0`, `stdout="hello\n"`, `stderr=""`
- **When** `run_shell("echo hello")` is called
- **Then** the result SHALL be `{"exit_code": 0, "stdout": "hello\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd parameter

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` SHALL be called with `cwd="/tmp"`

#### Scenario: LocalTransport.run_shell forwards timeout parameter

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", timeout=30)` is called
- **Then** `subprocess.run` SHALL be called with `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data parameter

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` SHALL be called with `input="hello"`

#### Scenario: LocalTransport.run_shell uses shell=True and captures output

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("echo hi")` is called
- **Then** `subprocess.run` SHALL be called with `shell=True`, `capture_output=True`, and `text=True`

