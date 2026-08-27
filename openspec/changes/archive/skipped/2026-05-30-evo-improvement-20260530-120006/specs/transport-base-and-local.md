# Transport Base Class and LocalTransport

## ADDED Requirements

### Requirement: Transport base class contract

`Transport` SHALL define two methods: `run_shell(cmd, cwd, timeout, stdin_data)` and `close()`.
Calling `run_shell()` on the base class SHALL raise `NotImplementedError`.
Calling `close()` on the base class SHALL execute without error (no-op).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` base class instance
- **When** `run_shell("echo hi")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close is a no-op

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` base class instance
- **When** `close()` is called
- **Then** no exception is raised

### Requirement: LocalTransport.run_shell delegates to subprocess

`LocalTransport` SHALL override `run_shell` to invoke `subprocess.run` with
`shell=True`, `capture_output=True`, `text=True`, forwarding `cwd`, `timeout`,
and `input` (from `stdin_data`). It SHALL return a dict with keys
`exit_code`, `stdout`, `stderr` matching the subprocess result.

#### Scenario: LocalTransport.run_shell returns dict from subprocess

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return `returncode=0, stdout="ok", stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result dict is `{"exit_code": 0, "stdout": "ok", "stderr": ""}`

#### Scenario: LocalTransport.run_shell forwards cwd and timeout

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return a successful result
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"` and `timeout=30`

#### Scenario: LocalTransport.run_shell forwards stdin_data as input

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to return a successful result
- **When** `run_shell("cat", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `input="hello"`

