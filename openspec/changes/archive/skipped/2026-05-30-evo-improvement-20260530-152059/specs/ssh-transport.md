# ssh-transport

## ADDED Requirements

### Requirement: SSHTransport stores configuration and expands key_path

`SSHTransport.__init__` SHALL store `host`, `user`, `port`, and expand
`key_path` via `Path.expanduser()`. If `key_path` is `None`, the attribute
SHALL remain `None`.

#### Scenario: Constructor stores all SSH parameters

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="server.example.com", user="alice", port=2222,
      key_path="/home/alice/.ssh/id_rsa")` is constructed
- **Then** `.host` is `"server.example.com"`, `.user` is `"alice"`,
      `.port` is `2222`, `.key_path` is the expanded form of the path

#### Scenario: Constructor defaults user to None and port to 22

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** no preconditions
- **When** `SSHTransport(host="myhost")` is constructed
- **Then** `.user` is `None`, `.port` is `22`, `.key_path` is `None`

### Requirement: SSHTransport._target builds remote address string

`_target()` SHALL return `"user@host"` when `user` is set, otherwise `"host"`.

#### Scenario: _target with user returns user@host

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"` and `user="bob"`
- **When** `_target()` is called
- **Then** the result is `"bob@myhost"`

#### Scenario: _target without user returns host only

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** an `SSHTransport` with `host="myhost"` and `user=None`
- **When** `_target()` is called
- **Then** the result is `"myhost"`

### Requirement: SSHTransport._base_args builds SSH argument list

`_base_args()` SHALL return a list beginning with `"ssh"` and
`"StrictHostKeyChecking=no"`. When `port` is not 22, it MUST include `-p <port>`.
When `key_path` is set, it MUST include `-i <key_path>`.

#### Scenario: _base_args with default port omits -p flag

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="myhost"`, `port=22`
- **When** `_base_args()` is called
- **Then** the result does not contain `"-p"`

#### Scenario: _base_args with non-default port includes -p

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="myhost"`, `port=2222`
- **When** `_base_args()` is called
- **Then** the result contains `"-p"` followed by `"2222"`

#### Scenario: _base_args with key_path includes -i

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="myhost"`, `key_path="/home/bob/.ssh/key"`
- **When** `_base_args()` is called
- **Then** the result contains `"-i"` followed by `"/home/bob/.ssh/key"`

#### Scenario: _base_args without key_path omits -i

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** an `SSHTransport` with `host="myhost"`, `key_path=None`
- **When** `_base_args()` is called
- **Then** the result does not contain `"-i"`

### Requirement: SSHTransport.run_shell executes remote commands via subprocess

`run_shell` SHALL call `subprocess.run` with SSH arguments. When `cwd` is
provided, it MUST prepend `cd '<cwd>' &&` to the command. On
`subprocess.TimeoutExpired`, it SHALL return `{"exit_code": -1, "stdout": "",
"stderr": "Timeout after <timeout>s"}`. On any other exception, it SHALL return
`{"exit_code": -1, "stdout": "", "stderr": "<exception message>"}`.

#### Scenario: run_shell with cwd prepends cd prefix

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `host="myhost"` and `subprocess.run` is mocked
      to return `returncode=0`, `stdout=""`, `stderr=""`
- **When** `run_shell("ls", cwd="/var/log")` is called
- **Then** the last argument to `subprocess.run` includes `"cd '/var/log' && ls"`

#### Scenario: run_shell without cwd passes command directly

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `host="myhost"` and `subprocess.run` is mocked
- **When** `run_shell("ls")` is called
- **Then** the last argument to `subprocess.run` is `"ls"` (no cd prefix)

#### Scenario: run_shell handles subprocess timeout gracefully

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `host="myhost"` and `subprocess.run` is mocked
      to raise `subprocess.TimeoutExpired(cmd="ssh", timeout=10)`
- **When** `run_shell("slow_cmd", timeout=10)` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr":
      "Timeout after 10s"}`

#### Scenario: run_shell handles generic exception gracefully

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** an `SSHTransport` with `host="myhost"` and `subprocess.run` is mocked
      to raise `OSError("connection refused")`
- **When** `run_shell("cmd")` is called
- **Then** the result is `{"exit_code": -1, "stdout": "", "stderr":
      "connection refused"}`

### Requirement: SSHTransport.close terminates control master

`close` SHALL execute `ssh -O exit` to shut down the control master when a
control path exists. If `_control_path` is `None`, it SHALL be a no-op.

#### Scenario: close with active control path sends exit command

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path="/tmp/zsiga_ssh_abc"` and
      `subprocess.run` is mocked
- **When** `close()` is called
- **Then** `subprocess.run` is called with args containing `"-O"` and `"exit"`,
      and `_control_path` is set to `None`

#### Scenario: close without control path is a no-op

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** an `SSHTransport` with `_control_path=None`
- **When** `close()` is called
- **Then** `subprocess.run` is not called and `_control_path` remains `None`
