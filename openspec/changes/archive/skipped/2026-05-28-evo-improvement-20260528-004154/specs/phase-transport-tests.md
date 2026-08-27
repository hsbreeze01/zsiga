# phase-transport-tests — Transport 模块单元测试覆盖

## ADDED Requirements

### Requirement: Transport 抽象基类行为

`Transport` 基类 SHALL 定义 `run_shell` 和 `close` 两个方法。
调用 `Transport().run_shell(...)` SHALL 抛出 `NotImplementedError`。
调用 `Transport().close()` SHALL 不抛异常（无操作）。

#### Scenario: Transport.run_shell raises NotImplementedError

- **testable**: true
- **target**: zsiga/transport.py::Transport.run_shell
- **Given** 一个 `Transport` 基类实例
- **When** 调用 `run_shell("echo hi")`
- **Then** SHALL 抛出 `NotImplementedError`

#### Scenario: Transport.close is no-op

- **testable**: true
- **target**: zsiga/transport.py::Transport.close
- **Given** 一个 `Transport` 基类实例
- **When** 调用 `close()`
- **Then** SHALL 正常返回，不抛异常

---

### Requirement: LocalTransport 封装 subprocess.run

`LocalTransport.run_shell` SHALL 将命令通过 `subprocess.run(shell=True, capture_output=True, text=True)` 执行，并返回包含 `exit_code`、`stdout`、`stderr` 三个 key 的字典。
参数 `cwd`、`timeout`、`stdin_data` SHALL 透传给 `subprocess.run`。

#### Scenario: LocalTransport.run_shell returns structured result

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** 一个 `LocalTransport` 实例，`subprocess.run` 被 mock 为返回 `returncode=0, stdout="ok\n", stderr=""` 的 CompletedProcess
- **When** 调用 `run_shell("echo ok")`
- **Then** SHALL 返回 `{"exit_code": 0, "stdout": "ok\n", "stderr": ""}`

#### Scenario: LocalTransport.run_shell passes cwd and timeout

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell
- **Given** 一个 `LocalTransport` 实例，`subprocess.run` 被 mock
- **When** 调用 `run_shell("ls", cwd="/tmp", timeout=30)`
- **Then** `subprocess.run` SHALL 被调用且参数包含 `shell=True, cwd="/tmp", timeout=30, capture_output=True, text=True`

---

### Requirement: SSHTransport 属性初始化

`SSHTransport.__init__` SHALL 将 `host`、`user`、`port`、`key_path` 存储为实例属性。
`key_path` SHALL 通过 `Path.expanduser()` 展开并转为字符串。
`_control_path` SHALL 初始为 `None`。

#### Scenario: SSHTransport init stores attributes

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.__init__
- **Given** 调用 `SSHTransport(host="server.example", user="admin", port=2222, key_path="~/.ssh/id_rsa")`
- **Then** 实例 SHALL 具有 `host="server.example"`, `user="admin"`, `port=2222`, `key_path` 为展开后的路径, `_control_path=None`

---

### Requirement: SSHTransport._target 返回目标字符串

`_target` SHALL 返回 `user@host` 格式字符串（当 user 非 None）。
当 user 为 None 时 SHALL 仅返回 host。

#### Scenario: SSHTransport._target with user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** 一个 `SSHTransport(host="srv", user="bob")` 实例
- **When** 调用 `_target()`
- **Then** SHALL 返回 `"bob@srv"`

#### Scenario: SSHTransport._target without user

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._target
- **Given** 一个 `SSHTransport(host="srv", user=None)` 实例
- **When** 调用 `_target()`
- **Then** SHALL 返回 `"srv"`

---

### Requirement: SSHTransport._base_args 构造参数列表

`_base_args` SHALL 返回以 `"ssh"` 开头的参数列表。
列表 SHALL 包含 `StrictHostKeyChecking=no`、`ControlPath` 参数。
当 `port != 22` 时 SHALL 包含 `-p <port>` 参数。
当 `key_path` 非 None 时 SHALL 包含 `-i <key_path>` 参数。

#### Scenario: SSHTransport._base_args with custom port and key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** 一个 `SSHTransport(host="srv", port=2222, key_path="/home/u/.ssh/key")` 实例
- **When** 调用 `_base_args()`
- **Then** 返回列表 SHALL 包含 `-p`, `2222`, `-i`, `/home/u/.ssh/key`

#### Scenario: SSHTransport._base_args with default port and no key

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._base_args
- **Given** 一个 `SSHTransport(host="srv")` 实例
- **When** 调用 `_base_args()`
- **Then** 返回列表 SHALL NOT 包含 `-p` 或 `-i`

---

### Requirement: SSHTransport.run_shell 执行远程命令

`SSHTransport.run_shell` SHALL 先调用 `_ensure_control()`，然后通过 `_base_args()` + target 构造 SSH 命令并执行。
当 `cwd` 非 None 时 SHALL 在远程执行 `cd '<cwd>' && <cmd>`。
当 `subprocess.TimeoutExpired` 时 SHALL 返回 `{"exit_code": -1, "stdout": "", "stderr": "Timeout after <timeout>s"}`。
其他异常 SHALL 返回 `{"exit_code": -1, "stdout": "", "stderr": str(e)}`。

#### Scenario: SSHTransport.run_shell with cwd prepends cd

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** 一个 `SSHTransport(host="srv")` 实例，`subprocess.run` 被 mock（包括 `_ensure_control` 内部调用）
- **When** 调用 `run_shell("ls", cwd="/app")`
- **Then** `subprocess.run` 的最后一个列表参数 SHALL 以 `"cd '/app' && ls"` 结尾

#### Scenario: SSHTransport.run_shell handles timeout

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.run_shell
- **Given** 一个 `SSHTransport(host="srv")` 实例，`subprocess.run` 在第二次调用时抛出 `subprocess.TimeoutExpired`
- **When** 调用 `run_shell("sleep 999", timeout=5)`
- **Then** SHALL 返回 `{"exit_code": -1, "stdout": "", "stderr": "Timeout after 5s"}`

---

### Requirement: SSHTransport.close 关闭 ControlMaster

`SSHTransport.close` SHALL 当 `_control_path` 非 None 时通过 ssh `-O exit` 关闭 ControlMaster，并将 `_control_path` 置为 `None`。
当 `_control_path` 为 None 时 SHALL 无操作。

#### Scenario: SSHTransport.close with active control

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport.close
- **Given** 一个 `SSHTransport(host="srv")` 实例，其 `_control_path` 已设为 `/tmp/zsiga_ssh_abc`
- **When** 调用 `close()`
- **Then** `subprocess.run` SHALL 被调用且参数包含 `-O`, `exit`；且 `_control_path` SHALL 变为 `None`

---

### Requirement: create_transport 工厂函数

`create_transport` SHALL 接受一个 `target_config` 对象。
当 `target_config.ssh` 为 falsy 时 SHALL 返回 `LocalTransport` 实例。
当 `target_config.ssh` 非 falsy 时 SHALL 返回 `SSHTransport` 实例，其参数取自 `target_config.ssh` 的 `host`、`user`、`port`、`key_path`。

#### Scenario: create_transport returns LocalTransport without ssh

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** 一个 `target_config` mock 对象，其 `ssh` 属性为 `None`
- **When** 调用 `create_transport(target_config)`
- **Then** SHALL 返回 `LocalTransport` 的实例

#### Scenario: create_transport returns SSHTransport with ssh config

- **testable**: true
- **target**: zsiga/transport.py::create_transport
- **Given** 一个 `target_config` mock 对象，其 `ssh` 属性为含 `host="srv", user="u", port=22, key_path=None` 的对象
- **When** 调用 `create_transport(target_config)`
- **Then** SHALL 返回 `SSHTransport` 实例，且 `host` 为 `"srv"`, `user` 为 `"u"`
