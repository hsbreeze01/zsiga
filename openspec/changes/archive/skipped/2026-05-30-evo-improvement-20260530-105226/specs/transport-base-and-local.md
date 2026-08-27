# transport-base-and-local

## ADDED Requirements

### Requirement: Transport base class contract tests

`tests/test_transport.py` SHALL contain a `TestTransportBase` test class that verifies the
abstract contract of `Transport`:

- `run_shell` raises `NotImplementedError` when called on the base class.
- `close` returns `None` and does not raise.

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` base instance
- **When** `run_shell("echo")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close returns None

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` base instance
- **When** `close()` is called
- **Then** no exception is raised and the return value is `None`

---

### Requirement: LocalTransport subprocess delegation tests

`tests/test_transport.py` SHALL contain a `TestLocalTransport` test class that covers
`LocalTransport.run_shell` using mocked `subprocess.run`:

- Successful execution returns `{exit_code, stdout, stderr}` extracted from the
  `subprocess.CompletedProcess` return value.
- `subprocess.TimeoutExpired` is NOT caught by `LocalTransport` (it propagates to caller).
- `cwd` and `stdin_data` kwargs are forwarded to `subprocess.run`.

#### Scenario: LocalTransport.run_shell returns structured result on success

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** `subprocess.run` is mocked to return `CompletedProcess(returncode=0, stdout="ok\n", stderr="")`
- **When** `LocalTransport().run_shell("echo ok")` is called
- **Then** the result dict equals `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell propagates TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** `subprocess.run` is mocked to raise `subprocess.TimeoutExpired("cmd", 120)`
- **When** `LocalTransport().run_shell("sleep 999")` is called
- **Then** `subprocess.TimeoutExpired` propagates (uncaught)

#### Scenario: LocalTransport.run_shell forwards cwd and stdin_data

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** `subprocess.run` is mocked to return a successful `CompletedProcess`
- **When** `LocalTransport().run_shell("ls", cwd="/tmp", stdin_data="hello")` is called
- **Then** `subprocess.run` is called with `shell=True, cwd="/tmp", capture_output=True, text=True, timeout=120, input="hello"`
