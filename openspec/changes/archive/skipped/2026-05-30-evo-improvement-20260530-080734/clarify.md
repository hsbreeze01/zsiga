# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行，1 个工厂函数，3 个类）编写单元测试文件 `tests/test_transport.py`，使用 mock 隔离 `subprocess.run` 等外部依赖，确保所有公开 API 有基本覆盖。

### 拆解后的子任务

- [ ] 1. **Transport 基类 + LocalTransport 测试** (预估复杂度：低, 预估 token：~2500 / 无历史参考)
  - 文件范围：`tests/test_transport.py`（新建），读取 `zsiga/transport.py` L6-L24
  - 覆盖：`Transport.run_shell` 抛 `NotImplementedError`、`Transport.close` 无异常、`LocalTransport.run_shell` mock `subprocess.run` 验证返回值 `{exit_code, stdout, stderr}` 和 `shell=True` 参数

- [ ] 2. **SSHTransport 全方法测试** (预估复杂度：中, 预估 token：~4500 / 无历史参考)
  - 文件范围：`tests/test_transport.py`，读取 `zsiga/transport.py` L27-L83
  - 覆盖：`__init__` 参数存储/默认值、`_target()` 格式化 `user@host`、`_base_args()` SSH 参数构建、`_ensure_control` mock `tempfile.mktemp` + `subprocess.run`、`run_shell` cwd 拼接/超时/异常处理、`close` 控制路径清理与 noop

- [ ] 3. **create_transport 工厂函数测试** (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - 文件范围：`tests/test_transport.py`，读取 `zsiga/transport.py` L86-L95
  - 覆盖：`target_config.ssh` 存在时返回 `SSHTransport`、不存在时返回 `LocalTransport`，用 `SimpleNamespace` 模拟 config

- [ ] 4. **验证测试全部通过** (预估复杂度：低, 预估 token：~1000 / 无历史参考)
  - 执行 `python -m pytest tests/test_transport.py` 确认退出码 0
  - 执行 `ruff check tests/test_transport.py` 确认无 lint 问题

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含 ≥8 个 `def test_` 函数
- 覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 全部公开方法
- 使用 `unittest.mock.patch` 隔离 `subprocess.run`、`tempfile.mktemp` 等外部调用
- 参考 `archive/skipped/2026-05-30-evo-improvement-20260530-043915/tests/test_spec_...__transport_base_class.py`（253 行，最完整版本）作为实现蓝本

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改其他测试文件或 conftest
- 不涉及集成测试或真实 SSH/本地命令执行
- 不引入新依赖

### 依赖的外部条件
- `zsiga/transport.py` 在当前形态下不变（96 行，3 类 1 函数）
- 项目 `unittest.mock` 可用（标准库）
- `pytest` 框架可用
- 已有归档测试实现可复用测试模式（`@patch("zsiga.transport.subprocess.run")` 模式）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥8 个 `def test_` 函数
2. 测试覆盖全部 4 个公开符号：`Transport`、`LocalTransport`、`SSHTransport`、`create_transport`
3. `python -m pytest tests/test_transport.py` 退出码 0
4. `ruff check tests/test_transport.py` 无报错
5. 测试中无真实 `subprocess.run` 调用（全部 mock 隔离）

### 验收方式
- `grep -c "def test_" tests/test_transport.py` ≥ 8
- `python -m pytest tests/test_transport.py -v` 全部 PASSED
- `ruff check tests/test_transport.py` 退出码 0
- 归档实现蓝本中的核心测试模式（mock subprocess、SimpleNamespace config）被复用

## 约束

### 不能修改的文件
- `zsiga/transport.py` — 仅读取分析，不做任何改动
- `tests/conftest_zsiga.py` — 不修改现有 conftest
- `zsiga/` 下所有源码文件

### 项目部署分支
- deploy（主开发分支）

### 已知风险
- **历史空转风险**：该提案已出现 15+ 次，全部被 skip/archive，从未成功通过 verify。根因多为 verify 阶段失败或 deploy branch drift。需确保实现一次性通过 pytest + ruff 检查
- **SSHTransport 测试复杂度**：SSHTransport 有 6 个方法，`_ensure_control` 涉及 `tempfile.mktemp` 和 `subprocess.run` 双 mock，需仔细处理 mock 顺序和副作用
- **subprocess mock 精确性**：`LocalTransport` 和 `SSHTransport` 都调用 `subprocess.run` 但参数不同，需用精确的 `@patch` 路径隔离

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（同类任务从未成功完成，基于归档蓝本文件规模估算）
