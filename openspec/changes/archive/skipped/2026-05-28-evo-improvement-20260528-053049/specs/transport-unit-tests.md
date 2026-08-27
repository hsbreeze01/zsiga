# transport-unit-tests

## ADDED Requirements

### Requirement: Transport base class defines abstract shell interface

`Transport` SHALL define `run_shell` and `close`. Calling `run_shell` on the
base class directly MUST raise `NotImplementedError`. `close` on the base
class SHALL be a safe no-op (returns `None`, never raises).

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** a `Transport` instance
- **When** `run_shell("ls")` is called
- **Then** `NotImplementedError` is raised

#### Scenario: Transport.close is a no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** a `Transport` instance
- **When** `close()` is called
- **Then** it returns `None` without raising

---

### Requirement: LocalTransport wraps subprocess.run for local execution

`LocalTransport.run_shell` SHALL delegate to `subprocess.run` with
`shell=True` and `capture_output=True, text=True`. It MUST return a dict
with keys `exit_code` (int), `stdout` (str), `stderr` (str) reflecting the
completed process result.

#### Scenario: LocalTransport.run_shell returns subprocess result on success

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to
  return `returncode=0`, `stdout="ok\n"`, `stderr=""`
- **When** `run_shell("echo ok")` is called
- **Then** the result dict equals `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell propagates non-zero exit code

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to
  return `returncode=1`, `stdout=""`, `stderr="fail"`
- **When** `run_shell("false")` is called
- **Then** the result dict equals `{"exit_code": 1, "stdout": "", "stderr": "fail"}`

#### Scenario: LocalTransport.run_shell passes cwd and timeout to subprocess

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** a `LocalTransport` instance and `subprocess.run` is mocked to
  capture its call kwargs
- **When** `run_shell("ls", cwd="/tmp", timeout=30)` is called
- **Then** `subprocess.run` is called with `cwd="/tmp"` and `timeout=30`

---

### Requirement: SSHTransport manages an SSH control channel

`SSHTransport` SHALL establish an SSH multiplexed control master on first
use and reuse it for subsequent commands. It MUST store host, user, port,
key_path and expand `~` in key_path.

#### Scenario: SSHTransport.__init__ stores parameters and expands key_path

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is constructed with `host="srv"`, `user="bob"`, `port=2222`, `key_path="~/id_rsa"`
- **When** attributes are inspected
- **Then** `host` is `"srv"`, `user` is `"bob"`, `port` is `2222`, `key_path` ends with `"/id_rsa"` (tilde expanded), and `_control_path` is `None`

#### Scenario: SSHTransport._target returns user@host when user is set

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"` and `user="alice"`
- **When** `_target()` is called
- **Then** it returns `"alice@srv"`

#### Scenario: SSHTransport._target returns bare host when user is None

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv"` and `user=None`
- **When** `_target()` is called
- **Then** it returns `"srv"`

#### Scenario: SSHTransport._base_args includes ControlPath and custom port

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222`, `key_path="/key"`, and `_control_path="/tmp/ctl"`
- **When** `_base_args()` is called
- **Then** the returned list contains `"ControlPath=/tmp/ctl"`, `"-p"`, `"2222"`, `"-i"`, `"/key"`

#### Scenario: SSHTransport._base_args omits port flag when port is default 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=22` and `_control_path="/tmp/ctl"`
- **When** `_base_args()` is called
- **Then** the returned list does not contain `"-p"`

#### Scenario: SSHTransport._ensure_control calls subprocess on first invocation

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is called once with args starting with `"ssh"` and ending with `"true"`, and `_control_path` is set to a non-None value

#### Scenario: SSHTransport._ensure_control is idempotent

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control
- **Given** an `SSHTransport` with `_control_path` already set and `subprocess.run` mocked
- **When** `_ensure_control()` is called
- **Then** `subprocess.run` is not called

#### Scenario: SSHTransport.run_shell handles subprocess.TimeoutExpired

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked as no-op and `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
- **When** `run_shell("slow_cmd", timeout=5)` is called
- **Then** the result dict equals `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}`

#### Scenario: SSHTransport.run_shell prepends cwd via cd command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked as no-op and `subprocess.run` mocked to return success
- **When** `run_shell("ls", cwd="/home/user/project")` is called
- **Then** the last argument to `subprocess.run` contains `"cd '/home/user/project' && ls"`

#### Scenario: SSHTransport.run_shell returns success result from subprocess

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked as no-op and `subprocess.run` mocked to return `returncode=0`, `stdout="files\n"`, `stderr=""`
- **When** `run_shell("ls")` is called
- **Then** the result dict equals `{"exit_code": 0, "stdout": "files\n", "stderr": ""}`

#### Scenario: SSHTransport.close sends ssh -O exit

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/ctl"` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"` and `"exit"`, and `_control_path` is reset to `None`

#### Scenario: SSHTransport.close is no-op when no control channel

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None` and `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is not called

---

### Requirement: create_transport factory routes by target config

`create_transport` SHALL return `LocalTransport` when `target_config` has no
`ssh` attribute (or it is falsy) and `SSHTransport` when `ssh` is present.

#### Scenario: create_transport returns LocalTransport for config without ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with no `ssh` attribute
- **When** `create_transport(config)` is called
- **Then** the returned instance is a `LocalTransport`

#### Scenario: create_transport returns SSHTransport for config with ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object whose `ssh` attribute has `host="srv"`, `user=None`, `port=22`, `key_path=None`
- **When** `create_transport(config)` is called
- **Then** the returned instance is an `SSHTransport` with `host="srv"`

#### Scenario: create_transport returns LocalTransport when ssh attribute is falsy

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** a config object with `ssh=None`
- **When** `create_transport(config)` is called
- **Then** the returned instance is a `LocalTransport`
