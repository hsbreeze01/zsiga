# ssh-transport.md — Delta Spec

## ADDED Requirements

### Requirement: SSHTransport construction and attribute storage

`SSHTransport.__init__(host, user, port, key_path)` SHALL store `host`, `user`,
`port`, and `key_path` as instance attributes. When `key_path` is provided, it
MUST be resolved via `Path.expanduser()`. The `_control_path` attribute SHALL be
initialized to `None`.

#### Scenario: SSHTransport stores constructor arguments

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is instantiated with `host="srv.example.com"`,
  `user="deploy"`, `port=2222`, `key_path="~/.ssh/id_rsa"`
- **When** the instance attributes are inspected
- **Then** `host` is `"srv.example.com"`, `user` is `"deploy"`, `port` is `2222`,
  `key_path` ends with `"/.ssh/id_rsa"` (expanded), and `_control_path` is `None`

#### Scenario: SSHTransport default port and optional fields

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** `SSHTransport` is instantiated with only `host="srv.example.com"`
- **When** the instance attributes are inspected
- **Then** `user` is `None`, `port` is `22`, `key_path` is `None`, `_control_path` is `None`

---

### Requirement: SSHTransport._target constructs SSH target string

`_target()` SHALL return `"{user}@{host}"` when `user` is set, otherwise just `host`.

#### Scenario: _target with user returns user@host

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv.example.com"` and `user="deploy"`
- **When** `_target()` is called
- **Then** the result is `"deploy@srv.example.com"`

#### Scenario: _target without user returns host only

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="srv.example.com"` and `user=None`
- **When** `_target()` is called
- **Then** the result is `"srv.example.com"`

---

### Requirement: SSHTransport._base_args builds SSH argument list

`_base_args()` SHALL return a list beginning with `ssh` and `StrictHostKeyChecking=no`.
When `port` is not `22`, it MUST include `-p {port}`. When `key_path` is set, it
MUST include `-i {key_path}`.

#### Scenario: _base_args includes port when non-default

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=2222`, `key_path=None`
- **When** `_base_args()` is called
- **Then** the result contains `-p` and `2222`

#### Scenario: _base_args includes identity file when key_path set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `port=22`, `key_path="/home/user/.ssh/id_rsa"`
- **When** `_base_args()` is called
- **Then** the result contains `-i` and `"/home/user/.ssh/id_rsa"`

---

### Requirement: SSHTransport.run_shell executes remote command via SSH

`SSHTransport.run_shell` MUST call `_ensure_control()` before executing, then
invoke `subprocess.run` with the SSH args and remote command. When `cwd` is provided,
the remote command SHALL be prefixed with `cd '<cwd>' && `. On
`subprocess.TimeoutExpired`, it MUST return `{"exit_code": -1, "stdout": "", "stderr": "Timeout after <timeout>s"}`.

#### Scenario: SSHTransport.run_shell prefixes cwd into remote command

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked (no-op) and
  `subprocess.run` mocked to return `returncode=0`, `stdout="out"`, `stderr=""`
- **When** `run_shell("ls", cwd="/home/deploy")` is called
- **Then** the subprocess args list contains `"cd '/home/deploy' && ls"` as the
  last element

#### Scenario: SSHTransport.run_shell handles timeout

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked (no-op) and
  `subprocess.run` mocked to raise `subprocess.TimeoutExpired`
- **When** `run_shell("sleep 999", timeout=1)` is called
- **Then** the returned dict is `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 1s"}`

#### Scenario: SSHTransport.run_shell handles generic exception

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `_ensure_control` mocked (no-op) and
  `subprocess.run` mocked to raise `OSError("network error")`
- **When** `run_shell("cmd")` is called
- **Then** the returned dict has `exit_code` equal to `-1` and `stderr` containing
  `"network error"`

---

### Requirement: SSHTransport.close tears down control master

`SSHTransport.close()` SHALL execute `ssh -O exit <target>` via subprocess to
tear down the control master when `_control_path` is set, and reset `_control_path`
to `None`. When `_control_path` is `None`, `close()` SHALL be a no-op.

#### Scenario: SSHTransport.close sends exit to control master

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/zsiga_ssh_abc"` and
  `subprocess.run` mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"`, `"exit"`, and
  `_control_path` becomes `None`

#### Scenario: SSHTransport.close is no-op when no control path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` is not called and `_control_path` remains `None`

