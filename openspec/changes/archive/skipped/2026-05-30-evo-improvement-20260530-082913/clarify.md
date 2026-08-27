# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行，1 函数 + 3 类）创建缺失的单元测试文件 `tests/test_transport.py`。该模块定义了传输层抽象（`Transport` 抽象基类、`LocalTransport` 本地执行、`SSHTransport` SSH 远程执行）及工厂函数 `create_transport()`，目前项目 `tests/` 目录下无对应测试文件。

### 拆解后的子任务

- [ ] 1. **Transport 基类 + LocalTransport 测试** (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - 文件范围：`tests/test_transport.py`（新建）
  - 覆盖：`Transport.run_shell` 抛 `NotImplementedError`；`Transport.close` 返回 `None`；`LocalTransport.run_shell` 调用 `subprocess.run` 时的返回结构、`cwd` 传递、`stdin_data` 传递、`timeout` 传递
  - Mock 策略：`@patch("zsiga.transport.subprocess.run")`

- [ ] 2. **SSHTransport 测试** (预估复杂度：中, 预估 token：~2500 / 无历史参考)
  - 文件范围：`tests/test_transport.py`（同上）
  - 覆盖：`__init__` 参数存储与 `~` 展开；`_target` 有/无 user 前缀；`_base_args` 端口/密钥组合；`_ensure_control` 幂等性（设置 `_control_path` 后不重复调用）；`run_shell` cwd 前缀/无 cwd/超时场景；`close` 有/无控制路径
  - Mock 策略：`subprocess.run` side_effect 双调用序列（`_ensure_control` + 实际命令）

- [ ] 3. **create_transport 工厂函数测试** (预估复杂度：低, 预估 token：~1000 / 无历史参考)
  - 文件范围：`tests/test_transport.py`（同上）
  - 覆盖：无 ssh 配置 → `LocalTransport`；ssh=None → `LocalTransport`；有 ssh 配置 → `SSHTransport` 且参数正确传递
  - Mock 策略：`types.SimpleNamespace(ssh=...)` 模拟 `target_config`

- [ ] 4. **全量 pytest 通过验证** (预估复杂度：低, 预估 token：~500 / 无历史参考)
  - 执行 `python -m pytest tests/test_transport.py` 确认退出码 0
  - 执行 `ruff check tests/test_transport.py` 确认无 lint 问题

## 边界

### IN scope
- 新建 `tests/test_transport.py`，覆盖 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的公开接口
- 使用 mock 隔离 `subprocess.run`，确保测试可独立运行
- 参考 `openspec/changes/evo-improvement-20260530-082913/tests/` 下已有蓝本的测试模式

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改任何其他现有文件
- 不涉及集成测试或端到端测试
- 不处理 SSH 连接的实际网络行为

### 依赖的外部条件
- `zsiga/transport.py` 模块可正常导入（无外部依赖缺失）
- `pytest` 和 `unittest.mock` 可用（项目已有测试基础设施）
- 项目 deploy branch 无外部冲突修改

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含 ≥ 20 个 `def test_` 函数
2. 测试覆盖全部 4 个公开符号：`Transport`、`LocalTransport`、`SSHTransport`、`create_transport`
3. `python -m pytest tests/test_transport.py` 退出码 0
4. `ruff check tests/test_transport.py` 无错误

### 验收方式
- BAC-01: 确认文件 `tests/test_transport.py` 存在
- BAC-02: grep `def test_create_transport` 存在于该文件
- BAC-03: 统计 `def test_` 函数数 ≥ 1
- BAC-04: `python -m pytest tests/test_transport.py` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/transport.py`（只读分析）
- 所有其他 `zsiga/` 下源码文件
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
deploy

### 已知风险
- **历史空转风险**：该提案在 `archive/skipped/` 中出现 15+ 次，均未成功落地。需确保本次测试文件直接写入 `tests/test_transport.py` 而非仅停留在 openspec 变更目录
- **测试蓝本已存在但未落地**：`openspec/changes/evo-improvement-20260530-082913/tests/` 下有 3 个参考测试文件（共 24 个测试函数），可直接参考其模式编写最终测试
- **deploy branch drift**：近期多次出现 deploy branch HEAD 在处理过程中变化的情况，需注意原子性提交

### 预估 token 消耗
- prompt: ~5500
- completion: ~3000
- 数据来源: 无历史参考（基于模块复杂度和测试数量估算）
