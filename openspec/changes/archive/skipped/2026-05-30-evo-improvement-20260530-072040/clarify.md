# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为无测试覆盖的模块 `zsiga/transport.py`（96 行，3 个类 + 1 个工厂函数）创建单元测试文件 `tests/test_transport.py`。模块包含传输层抽象基类 `Transport`、本地实现 `LocalTransport`、SSH 实现 `SSHTransport`，以及工厂函数 `create_transport(target_config)`。当前 `tests/` 目录下不存在 `test_transport.py`。

### 拆解后的子任务

- [ ] 1. **Transport 基类 + LocalTransport 测试** (预估复杂度：低, 预估 token：~3000 / 无历史参考)
  - 验证 `Transport.run_shell()` 抛出 `NotImplementedError`
  - 验证 `Transport.close()` 为空操作（不抛异常）
  - 验证 `LocalTransport.run_shell()` 正确调用 `subprocess.run(shell=True, capture_output=True, text=True)` 并返回 `{"exit_code", "stdout", "stderr"}` 格式
  - 验证 `LocalTransport.run_shell()` 的 `cwd`, `timeout`, `stdin_data` 参数透传
  - 文件范围：`tests/test_transport.py`（新建）

- [ ] 2. **SSHTransport 测试** (预估复杂度：中, 预估 token：~5000 / 无历史参考)
  - 验证 `__init__` 参数存储（host, user=None, port=22, key_path=None）
  - 验证 `_target` 属性拼接（user@host，无 user 时仅 host）
  - 验证 `_base_args` 端口/密钥条件注入逻辑
  - 验证 `_ensure_control` 幂等性（ControlMaster 已存在时不重复调用 subprocess）
  - 验证 `run_shell` 的 cwd 前缀拼接、`TimeoutExpired` 和 `OSError` 异常处理
  - 验证 `close` 发送 `-O exit` 信号及无 control_path 时静默退出
  - 全部使用 `unittest.mock.patch` mock `subprocess.run` 和 `tempfile.mktemp`
  - 文件范围：`tests/test_transport.py`（续写）

- [ ] 3. **create_transport 工厂函数测试** (预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 验证 `target_config` 无 `ssh` 属性时返回 `LocalTransport` 实例
  - 验证 `target_config.ssh` 为 `None` 时返回 `LocalTransport` 实例
  - 验证 `target_config.ssh` 存在时返回 `SSHTransport` 实例
  - 使用 `unittest.mock.MagicMock` 构造 `target_config` 对象
  - 文件范围：`tests/test_transport.py`（续写）

## 边界

### IN scope
- 创建 `tests/test_transport.py`，包含覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的单元测试
- 使用 mock 隔离所有外部依赖（`subprocess.run`、`tempfile.mktemp`）
- 确保 `pytest tests/test_transport.py` 退出码 0
- 满足全部 4 条 BAC

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改任何其他源文件
- 不添加集成测试或端到端测试
- 不涉及项目中已有的间接使用 `LocalTransport` 的其他测试文件

### 依赖的外部条件
- `zsiga/transport.py` 当前内容不变（96 行，3 类 + 1 函数）
- `pytest` 和 `unittest.mock` 可用（Python 3.10+ 标准库）
- `ruff` lint 通过（目标模块当前 0 lint 问题）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含至少 10 个 `def test_` 函数
2. 文件中包含 `test_create_transport` 函数（BAC-02）
3. 所有测试覆盖 3 个类的公开方法和工厂函数，包括正常路径与异常路径
4. `python -m pytest tests/test_transport.py` 退出码 0（BAC-04）
5. `ruff check tests/test_transport.py` 无错误

### 验收方式
- 文件存在性检查：`test -f tests/test_transport.py`
- 函数名存在性检查：`grep -c 'def test_' tests/test_transport.py` ≥ 10
- BAC-02 检查：`grep 'def test_create_transport' tests/test_transport.py`
- pytest 执行：`python -m pytest tests/test_transport.py -v`
- lint 检查：`ruff check tests/test_transport.py`

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- 所有其他 `zsiga/` 源码文件
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- `main`

### 已知风险
- **历史空转风险**：同名 `add-tests-transport` 提案已出现 15+ 次，全部被 skip/archive。本轮需确保 clarify 结构足够具体，避免再次空转。
- **SSHTransport mock 复杂度**：`SSHTransport` 内部依赖 `subprocess.run`（用于 ControlMaster 建立）和 `tempfile.mktemp`（生成 control socket 路径），mock 需精确匹配调用时序，否则测试可能因 mock 不匹配而失败。
- **归档蓝本可用性**：archive 中有之前生成的测试文件（`2026-05-30-evo-improvement-20260530-043915/tests/` 约 450 行），可作为参考但不能直接复制——需确认与当前 `transport.py` 源码的兼容性。

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类任务从未成功执行）
