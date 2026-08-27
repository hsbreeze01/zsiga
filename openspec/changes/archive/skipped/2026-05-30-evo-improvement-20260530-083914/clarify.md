# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试模块 `zsiga/transport.py`（96 行，1 个工厂函数 `create_transport`，3 个类 `Transport`/`LocalTransport`/`SSHTransport`）创建 `tests/test_transport.py`，使用 mock 隔离 subprocess 调用，确保全部测试可独立运行。

### 拆解后的子任务
- [ ] 1. **Transport 基类 + LocalTransport 测试** — 验证 `Transport.run_shell` 抛 `NotImplementedError`、`Transport.close` 为 no-op；mock `subprocess.run` 测试 `LocalTransport.run_shell` 的返回字典结构（exit_code/stdout/stderr）、参数透传（cwd/timeout）。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 2. **SSHTransport 全方法测试** — 覆盖 `__init__`（路径展开 `~`/`os.path.expanduser`）、`_ensure_control`（幂等性、subprocess 调用链）、`_base_args` 返回值、`_target` 属性、`run_shell`（cwd 前缀、超时透传、stdout/stderr 解析）、`close`（控制路径清理 subprocess 调用）。需 `side_effect` 列表模拟多次 subprocess 调用序列。（预估复杂度：中, 预估 token：~5000 / 无历史参考）
- [ ] 3. **create_transport 工厂函数测试** — 用 `SimpleNamespace` 模拟 `target_config`，验证 `target_config.ssh` 存在时返回 `SSHTransport` 实例、不存在时返回 `LocalTransport` 实例、类型正确性断言。（预估复杂度：低, 预估 token：~2000 / 无历史参考）

## 边界

### IN scope
- 创建 `tests/test_transport.py`，包含覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的单元测试
- 使用 `unittest.mock` 隔离 `subprocess.run` 调用
- 每个测试可独立运行，不依赖运行时环境或网络

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `zsiga/config.py` 或任何配置 dataclass
- 不添加集成测试（不测试真实 SSH 连接）
- 不创建 conftest fixture 文件

### 依赖的外部条件
- `zsiga/transport.py` 文件存在且结构稳定（96 行，3 类 1 函数）
- `unittest.mock` 可用（标准库）
- `pytest` 已安装（已确认 v9.0.3 在 venv 中）
- `subprocess.run` 可被 mock（标准库，无额外依赖）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥ 10 个 `def test_` 函数
2. `test_create_transport` 函数存在，验证工厂函数的两种分支
3. SSHTransport 测试覆盖全部 6 个方法（`__init__`、`_ensure_control`、`_base_args`、`_target`、`run_shell`、`close`）
4. `python -m pytest tests/test_transport.py` 退出码 0，无 skip/error
5. `ruff check tests/test_transport.py` 无 lint 错误

### 验收方式
- `ls tests/test_transport.py` 确认文件存在
- `grep -c "def test_" tests/test_transport.py` ≥ 10
- `grep "test_create_transport" tests/test_transport.py` 匹配成功
- `python -m pytest tests/test_transport.py -v` 全部 PASSED
- `ruff check tests/test_transport.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`
- `zsiga/config.py`
- `tests/conftest.py` 或任何已有测试文件
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
deploy

### 已知风险
- **历史空转风险**：同名提案已出现 15+ 次，全部 skip/archive，从未成功落地。根因可能是执行阶段 mock 复杂度（SSHTransport 内部链式调用 `_ensure_control` → `subprocess.run`），需确保 subprocess mock 的 `side_effect` 正确模拟多步调用序列
- **SSHTransport mock 复杂度**：`SSHTransport.__init__` 调用 `_ensure_control`，后者调用 `subprocess.run`；`SSHTransport.run_shell` 再次调用 `_ensure_control` + `subprocess.run`。需在 `setUp` 或 fixture 中正确配置 mock 的 `side_effect` 列表
- **Transport 基类抽象性**：`Transport.run_shell` 直接抛 `NotImplementedError`，需确认测试不意外实例化基类

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类任务从未成功完成）
