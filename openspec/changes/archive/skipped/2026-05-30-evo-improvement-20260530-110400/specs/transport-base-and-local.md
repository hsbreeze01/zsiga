# transport-base-and-local

## ADDED Requirements

### Requirement: Transport base class abstract interface

The `Transport` base class SHALL define `run_shell` as an abstract interface
that raises `NotImplementedError` when called directly, and `close` as a
no-op default.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("echo hi")` is called
- **Then** it SHALL raise `NotImplementedError`

#### Scenario: Transport.close is a no-op

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception SHALL be raised

### Requirement: LocalTransport delegates to subprocess.run

`LocalTransport` SHALL forward all parameters (`cmd`, `cwd`, `timeout`,
`stdin_data`) to `subprocess.run` with `shell=True`, `capture_output=True`,
and `text=True`, returning a dict with keys `exit_code`, `stdout`, `stderr`.

#### Scenario: LocalTransport.run_shell returns structured result

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is patched to return
  `returncode=0`, `stdout="ok"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result SHALL equal `{"exit_code": 0, "stdout": "ok", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd parameter

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is patched
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the patched `subprocess.run` SHALL be called with `cwd="/tmp"`

#### Scenario: LocalTransport.run_shell forwards timeout parameter

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is patched
- **When** `run_shell("ls", timeout=30)` is called
- **Then** the patched `subprocess.run` SHALL be called with `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data parameter

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is patched
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** the patched `subprocess.run` SHALL be called with `input="hello"`

#### Scenario: LocalTransport.run_shell calls subprocess with shell=True

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is patched
- **When** `run_shell("echo hi")` is called
- **Then** the patched `subprocess.run` SHALL be called with `shell=True`,
  `capture_output=True`, and `text=True`

#### Scenario: LocalTransport.run_shell propagates nonzero exit code

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is patched to return
  `returncode=1`, `stdout=""`, `stderr="fail"`
- **When** `run_shell("false")` is called
- **Then** the result SHALL equal `{"exit_code": 1, "stdout": "", "stderr": "fail"}`

