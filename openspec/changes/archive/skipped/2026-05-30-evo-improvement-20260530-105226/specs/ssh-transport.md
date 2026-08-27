# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport full lifecycle tests

`tests/test_transport.py` SHALL contain a `TestSSHTransport` test class that covers the
full lifecycle using mocked `subprocess.run` and manual `_control_path` injection:

- `__init__` stores host, user, port, key_path (with `Path.expanduser`).
- `_target` returns `user@host` when user is set, or bare host otherwise.
- `_base_args` includes `-p` when port ≠ 22, `-i` when key_path is set, and always includes `StrictHostKeyChecking=no`.
- `_ensure_control` sets `_control_path` and invokes `subprocess.run` with control-master args.
- `run_shell` prepends `cd 'cwd' &&` when `cwd` is provided.
- `run_shell` translates `TimeoutExpired` to `exit_code=-1`.
- `close` sends `ssh -O exit` when `_control_path` is set, otherwise is a no-op.

#### Scenario: SSHTransport.__init__ stores configuration

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** SSHTransport is constructed with `host="h", user="u", port=2222, key_path="~/.ssh/id"`
- **Then** `.host == "h"`, `.user == "u"`, `.port == 2222`, `.key_path` is expanded from `~`, `._control_path is None`

#### Scenario: SSHTransport._target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an SSHTransport with `host="myhost"` and `user="root"`
- **When** `_target()` is called
- **Then** the result is `"root@myhost"`

#### Scenario: SSHTransport._target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an SSHTransport with `host="myhost"` and `user=None`
- **When** `_target()` is called
- **Then** the result is `"myhost"`

#### Scenario: SSHTransport._base_args includes port when non-default

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an SSHTransport with `port=2222` and `key_path="/key"`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"` and `"2222"` and `"-i"` and `"/key"`

#### Scenario: SSHTransport._base_args omits port when default

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an SSHTransport with `port=22` and `key_path=None`
- **When** `_base_args()` is called
- **Then** the result does NOT contain `"-p"`

#### Scenario: SSHTransport._ensure_control sets control_path and calls subprocess

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an SSHTransport with `_control_path=None` and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `_control_path` is set to a non-None value, and `subprocess.run` is called with args containing `"ControlMaster=auto"` and `"ControlPersist=600"`

#### Scenario: SSHTransport._ensure_control skips when already set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an SSHTransport with `_control_path="/tmp/ctrl"` and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is NOT called

#### Scenario: SSHTransport.run_shell prepends cwd when provided

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an SSHTransport with `_control_path` pre-set and `subprocess.run` mocked to return a successful result
- **When** `run_shell("ls", cwd="/home")` is called
- **Then** the last argument to `subprocess.run` includes `"cd '/home' && ls"`

#### Scenario: SSHTransport.run_shell handles TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an SSHTransport with `_control_path` pre-set and `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999")` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 120s"}`

#### Scenario: SSHTransport.run_shell handles generic exception

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an SSHTransport with `_control_path` pre-set and `subprocess.run` mocked to raise `OSError("conn refused")`
- **When** `run_shell("ls")` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr": "conn refused"}`

#### Scenario: SSHTransport.close sends exit command when control path is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an SSHTransport with `_control_path` set to `"/tmp/ctrl"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"` and `"exit"`, and `_control_path` becomes `None`

#### Scenario: SSHTransport.close is no-op when no control path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an SSHTransport with `_control_path` set to `None`
- **When** `close()` is called
- **Then** `subprocess.run` is not called and no exception is raised
