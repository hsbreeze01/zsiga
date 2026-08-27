# Spec: Transport Base Class & LocalTransport

## ADDED Requirements

### Requirement: Transport Base Class Abstract Contract

`Transport` SHALL be an abstract base class. Calling `run_shell()` on the base class MUST raise `NotImplementedError`. Calling `close()` on the base class MUST return `None`.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell

- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close

- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** the return value is `None`

---

### Requirement: LocalTransport.run_shell Delegates to subprocess.run

`LocalTransport.run_shell()` SHALL invoke `subprocess.run` with the provided `cmd`, `cwd`, `timeout`, and `stdin_data` arguments, and return a dict with keys `exit_code`, `stdout`, `stderr`.

#### Scenario: LocalTransport.run_shell returns exit_code stdout stderr dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** `subprocess.run` is mocked to return a `CompletedProcess(returncode=0, stdout="ok\n", stderr="")`
- **When** `LocalTransport().run_shell("echo ok")` is called
- **Then** the result is `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell passes cwd to subprocess

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** `subprocess.run` is mocked to return a `CompletedProcess(returncode=0, stdout="", stderr="")`
- **When** `LocalTransport().run_shell("ls", cwd="/tmp")` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"`

#### Scenario: LocalTransport.run_shell passes stdin_data as input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** `subprocess.run` is mocked to return a `CompletedProcess(returncode=0, stdout="", stderr="")`
- **When** `LocalTransport().run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

#### Scenario: LocalTransport.run_shell passes timeout to subprocess

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** `subprocess.run` is mocked to return a `CompletedProcess(returncode=0, stdout="", stderr="")`
- **When** `LocalTransport().run_shell("ls", timeout=30)` is called
- **Then** `subprocess.run` is called with `timeout=30`

#### Scenario: LocalTransport.run_shell calls subprocess with shell=True and capture_output

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** `subprocess.run` is mocked to return a `CompletedProcess(returncode=0, stdout="", stderr="")`
- **When** `LocalTransport().run_shell("echo")` is called
- **Then** `subprocess.run` is called with `shell=True`, `capture_output=True`, and `text=True`

