# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行，3 个类 + 1 个工厂函数）编写专属单元测试文件 `tests/test_transport.py`，覆盖全部公开接口。该模块是项目中唯一缺少专属测试文件的核心模块。

### 拆解后的子任务

- [ ] 1. **Transport 基类 + LocalTransport 测试**（预估复杂度：低，预估 token：~2000）
  - Transport 基类：`run_shell` 抛 `NotImplementedError`，`close` 空操作
  - LocalTransport：`run_shell` 调用 `subprocess.run`，需 mock 隔离
  - 目标文件：`tests/test_transport.py`（新建）

- [ ] 2. **SSHTransport 类测试**（预估复杂度：中，预估 token：~3000）
  - 覆盖 `__init__`、`_ensure_control`、`_base_args`、`_target`、`run_shell`、`close`
  - 需 mock `subprocess.run` 模拟 SSH ControlMaster 生命周期
  - 目标文件：`tests/test_transport.py`

- [ ] 3. **create_transport 工厂函数测试**（预估复杂度：低，预估 token：~1500）
  - 根据 `target_config.ssh` 是否存在返回 `LocalTransport` 或 `SSHTransport`
  - 需构造 mock config 对象
  - 目标文件：`tests/test_transport.py`

- [ ] 4. **全量 pytest 通过验证**（预估复杂度：低，预估 token：~500）
  - `python -m pytest tests/test_transport.py` 退出码 0
  - ruff lint 无报错
  - 目标文件：`tests/test_transport.py`

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含 ≥10 个 `def test_` 函数
- 覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 全部公开方法
- 使用 `unittest.mock` 隔离 `subprocess.run`，确保测试无外部依赖
- 可参考 `archive/skipped/2026-05-30-evo-improvement-20260530-043915/tests/` 和 `archive/skipped/2026-05-30-evo-improvement-20260530-054103/tests/` 中的历史测试蓝本

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `tests/conftest.py` 或其他现有测试文件
- 不添加集成测试（如真实 SSH 连接）

### 依赖的外部条件
- `zsiga/transport.py` 模块结构稳定（96 行，3 类 + 1 函数）
- `unittest.mock`（标准库）可用
- pytest 框架已就绪

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥10 个 `def test_` 函数
2. 测试覆盖 `Transport.run_shell`（NotImplementedError）、`Transport.close`、`LocalTransport.run_shell`、`SSHTransport.__init__`、`SSHTransport._ensure_control`、`SSHTransport._base_args`、`SSHTransport._target`、`SSHTransport.run_shell`、`SSHTransport.close`、`create_transport` 的正常与边界场景
3. `python -m pytest tests/test_transport.py` 退出码 0，全部测试通过
4. `ruff check tests/test_transport.py` 无报错

### 验收方式
- [BAC-01] `tests/test_transport.py` 文件存在
- [BAC-02] 文件中包含 `test_create_transport` 函数
- [BAC-03] 文件中包含至少 10 个 `def test_` 函数
- [BAC-04] `python -m pytest tests/test_transport.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- 所有现有测试文件
- `tests/conftest.py`、`tests/conftest_zsiga.py`

### 项目部署分支
- deploy

### 已知风险
- **历史空转风险**：同名 `add-tests-transport` 提案已出现 12+ 次，全部被 skip/archive。本次需确保代码质量足够通过 verify 阶段
- **SSH mock 复杂度**：`SSHTransport._ensure_control` 涉及 `subprocess.run` 多次调用和文件路径构造，mock 需精确匹配调用序列
- **归档蓝本质量未知**：历史 archive 中的测试代码未经过 verify 验证，可能包含错误，仅作参考

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考（同类 proposal 从未成功交付）
