# transport-base-and-local.md — Delta Spec

## ADDED Requirements

### Requirement: Transport base class abstract contract

`Transport` SHALL define `run_shell(cmd, cwd, timeout, stdin_data)` and `close()`.
Calling `run_shell` on the base `Transport` class MUST raise `NotImplementedError`.
`close()` on the base class SHALL be a no-op (return `None`).

#### Scenario: Base Transport.run_shell raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance (the base class, not a subclass)
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Base Transport.close returns None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** no exception is raised and the return value is `None`

---

### Requirement: LocalTransport.run_shell delegates to subprocess

`LocalTransport.run_shell` MUST execute the given shell command via `subprocess.run`
with `shell=True`, `capture_output=True`, `text=True`, and the provided `cwd`,
`timeout`, and `stdin_data` arguments. It SHALL return a dict with keys
`exit_code` (int), `stdout` (str), and `stderr` (str) reflecting the subprocess result.

#### Scenario: LocalTransport.run_shell returns subprocess result

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return a
  `CompletedProcess` with `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the returned dict is `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell passes cwd and timeout to subprocess

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp", timeout=30, stdin_data="data")` is called
- **Then** `subprocess.run` is called with `shell=True`, `cwd="/tmp"`,
  `capture_output=True`, `text=True`, `timeout=30`, `input="data"`

#### Scenario: LocalTransport.run_shell captures non-zero exit code

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance with `subprocess.run` mocked to return a
  `CompletedProcess` with `returncode=127`, `stdout=""`, `stderr="command not found"`
- **When** `run_shell("badcmd")` is called
- **Then** the returned dict is `{"exit_code": 127, "stdout": "", "stderr": "command not found"}`

