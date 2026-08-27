# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行）编写单元测试文件 `tests/test_transport.py`，覆盖 3 个类（`Transport`、`LocalTransport`、`SSHTransport`）和 1 个工厂函数（`create_transport`）的公开接口。不修改源码。

### 拆解后的子任务

- [ ] 1. **LocalTransport 测试** — 验证 `run_shell` 通过 `subprocess.run` 正确执行本地命令并返回 `{"exit_code", "stdout", "stderr"}` 结构；mock `subprocess.run`，覆盖正常返回、非零退出码、超时场景。（预估复杂度：低, 预估 token：~2500 / 无历史参考）
- [ ] 2. **SSHTransport 测试** — 验证构造参数（host/user/port/key_path）正确存储；`_target()` 生成 `user@host` 或纯 `host`；`_base_args()` 返回含 ControlMaster 路径的参数列表；`_ensure_control` 和 `run_shell` 通过 mock subprocess 验证 SSH 命令组装；`close()` 发送正确的关闭命令；覆盖 TimeoutExpired 和通用异常两条错误路径。（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 3. **create_transport 工厂函数测试** — 验证 `target_config.ssh` 存在时返回 `SSHTransport`，为 `None` 时返回 `LocalTransport`；mock SSH 构造避免真实连接。（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 4. **Transport 基类测试** — 验证抽象接口签名存在（`run_shell`、`close`）；`close` 默认为 no-op。（预估复杂度：低, 预估 token：~800 / 无历史参考）

## 边界

### IN scope
- 创建 `tests/test_transport.py`，包含上述 4 组测试
- 使用 `unittest.mock` 隔离 `subprocess.run`，不依赖真实 SSH/本地命令执行
- 测试覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的公开接口

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不测试 `SSHTransport` 的真实 SSH 连接（仅 mock 验证）
- 不测试私有属性（如 `_control_path` 的路径生成细节），仅验证其被 `_base_args` 正确引用
- 不涉及 `zsiga/config.py` 中 `SSHConfig` / `TargetConfig` 的单元测试

### 依赖的外部条件
- `zsiga/transport.py` 导入路径和公开 API 不变
- `unittest.mock` 可用（标准库）
- pytest 测试框架可用

## 目标

### 成功标准
1. `tests/test_transport.py` 存在且包含 ≥ 8 个 `def test_` 函数
2. 覆盖 `create_transport` 工厂函数的两条分支（SSH / Local）
3. 覆盖 `SSHTransport.run_shell` 的正常路径 + TimeoutExpired 异常路径 + 通用异常路径
4. 覆盖 `LocalTransport.run_shell` 的正常路径 + 非零退出码路径
5. `python -m pytest tests/test_transport.py` 退出码 0

### 验收方式
- `grep -c 'def test_' tests/test_transport.py` 计数 ≥ 8
- `grep -q 'test_create_transport' tests/test_transport.py` 存在
- `python -m pytest tests/test_transport.py -v` 全部 PASSED
- `ruff check tests/test_transport.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`
- `zsiga/config.py`
- `tests/conftest.py`（除非新增 fixture）
- 所有其他已有测试文件

### 项目部署分支
- `main`

### 已知风险
- SSHTransport 内部依赖 `tempfile.mkdtemp` 生成 ControlMaster 路径，测试中需确保不泄漏临时目录（mock `subprocess.run` 可规避）
- `create_transport` 直接 `SSHTransport(...)` 构造实例，测试需 mock `SSHTransport.__init__` 或提供无副作用配置
- 历史上同类 proposal（add-tests-*）已被自演进引擎反复生成 18+ 次未落地，但本次为人工明确下发，风险可控

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考（基于模块 96 行、4 组测试的估算）
