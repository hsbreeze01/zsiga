# spec: ssh-transport

## ADDED Requirements

### Requirement: SSHTransport initialises connection parameters

`SSHTransport.__init__` SHALL accept `host`, `user` (default `None`), `port` (default `22`), `key_path` (default `None`). The `key_path` MUST be expanded via `Path.expanduser()` and converted to string. Internal `_control_path` SHALL be initialised to `None`.

#### Scenario: SSHTransport stores init params and expands key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** construction with `host="myhost"`, `user="alice"`, `port=2222`, `key_path="~/id_rsa"`
- **When** the instance is created
- **Then** `host` SHALL be `"myhost"`, `user` SHALL be `"alice"`, `port` SHALL be `2222`, `key_path` SHALL equal `str(Path("~/id_rsa").expanduser())`, and `_control_path` SHALL be `None`

#### Scenario: SSHTransport._target returns user@host when user provided

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"`, `user="alice"`
- **When** `_target()` is called
- **Then** the result SHALL be `"alice@myhost"`

#### Scenario: SSHTransport._target returns host only when user is None

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"`, `user=None`
- **When** `_target()` is called
- **Then** the result SHALL be `"myhost"`

#### Scenario: SSHTransport._base_args includes strict host checking disabled and key_path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=2222`, `key_path="/home/u/.ssh/id"`
- **When** `_base_args()` is called
- **Then** the result SHALL contain `"StrictHostKeyChecking=no"`, `"-p"`, `"2222"`, `"-i"`, `"/home/u/.ssh/id"`

#### Scenario: SSHTransport._base_args omits port when port is 22

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="h"`, `port=22`
- **When** `_base_args()` is called
- **Then** the result SHALL NOT contain `"-p"`

#### Scenario: SSHTransport.run_shell prepends cwd to command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` and `subprocess.run` mocked
- **When** `run_shell("ls", cwd="/tmp")` is called
- **Then** the last argument to `subprocess.run` SHALL be `"cd '/tmp' && ls"`

#### Scenario: SSHTransport.run_shell handles TimeoutExpired

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked and `subprocess.run` raising `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=5)` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}`

#### Scenario: SSHTransport.run_shell handles generic OSError

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked and `subprocess.run` raising `OSError("network down")`
- **When** `run_shell("ls")` is called
- **Then** the result SHALL equal `{"exit_code": -1, "stdout": "", "stderr": "network down"}`

#### Scenario: SSHTransport.close sends exit via control master

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/ctrl"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` SHALL be called with args containing `"-O", "exit"` and `_control_path` SHALL be set to `None`

#### Scenario: SSHTransport.close is no-op when no control path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` SHALL NOT be called and the method SHALL return `None`

#### Scenario: SSHTransport._ensure_control establishes control master

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` SHALL be set to a non-None value and `subprocess.run` SHALL be called once with args containing `"ControlMaster=auto"`

