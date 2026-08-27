# clarify.md — add-tests-transport

## 需求拆解

### 原始需求
为 `zsiga/transport.py`（96 行，1 个公开函数 `create_transport`，3 个类 `Transport` / `LocalTransport` / `SSHTransport`）新建单元测试文件 `tests/test_transport.py`，覆盖公开接口。不修改源码。

### 拆解后的子任务

- [ ] 1. **Transport 基类与 LocalTransport 测试** — 验证 `Transport` 抽象接口定义（`run_shell`, `close`）以及 `LocalTransport.run_shell` 的行为（subprocess 调用、返回值）。使用 mock 隔离 subprocess。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 2. **SSHTransport 全方法测试** — 覆盖 `__init__`（配置解析）、`_ensure_control`（控制目录创建）、`_base_args`（SSH 参数组装）、`_target`（目标地址格式化）、`run_shell`（远程命令执行）、`close`（连接关闭）。mock paramiko/subprocess 避免真实 SSH 连接。（预估复杂度：中, 预估 token：~5000 / 无历史参考）
- [ ] 3. **create_transport 工厂函数测试** — 验证根据 `target_config` 中的传输类型正确分发到 `LocalTransport` 或 `SSHTransport`，包括边界情况（无 transport 字段时的默认行为、未知类型时的异常处理）。（预估复杂度：低, 预估 token：~3000 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_transport.py`，包含针对 `Transport`、`LocalTransport`、`SSHTransport`、`create_transport` 的单元测试
- 使用 mock 隔离 subprocess / SSH 外部依赖
- 确保所有测试可独立运行，不依赖运行时环境

### OUT of scope
- 不修改 `zsiga/transport.py` 源码
- 不修改 `zsiga/config.py` 或其他模块
- 不涉及集成测试或端到端测试
- 不修改 `pyproject.toml`、`requirements.txt` 等构建配置

### 依赖的外部条件
- `zsiga/transport.py` 的公开 API 保持当前签名不变
- `TargetConfig` 数据类结构稳定（`transport` 字段、`ssh` 字段）
- `pytest` 和 `unittest.mock` 可用（项目已有 `ruff` 和 `ast-grep-py` 作为开发依赖）

## 目标

### 成功标准
1. `tests/test_transport.py` 文件存在且包含至少 3 个 `def test_` 函数
2. 存在名为 `test_create_transport` 的测试函数
3. `python -m pytest tests/test_transport.py` 退出码为 0
4. 测试覆盖 `Transport`、`LocalTransport`、`SSHTransport` 三个类和 `create_transport` 函数
5. 所有外部依赖（subprocess、SSH）通过 mock 隔离，无真实网络/进程调用

### 验收方式
- `test -f tests/test_transport.py` 确认文件存在
- `grep -c 'def test_' tests/test_transport.py` 确认测试函数数量 ≥ 3
- `grep 'test_create_transport' tests/test_transport.py` 确认工厂函数测试存在
- `python -m pytest tests/test_transport.py -v` 退出码 0 且全部 PASSED
- `python -m ruff check tests/test_transport.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/transport.py`（仅读取分析）
- `zsiga/config.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
- `zsiga/self-evolve`（自演进目标项目）

### 已知风险
- **历史空转风险**：同名 proposal `add-tests-transport` 已在 archive 中出现 20+ 次，全部 skipped。本轮需确保任务可落地，避免再次空转。
- **SSH mock 复杂度**：`SSHTransport` 内部使用 subprocess 调用 ssh 命令，需仔细 mock `subprocess.run` 避免测试环境依赖。
- **TargetConfig 依赖**：测试需构造 `TargetConfig` 实例，需确认其字段结构（可能需要从 `zsiga.config` 导入）。

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考（基于模块规模 96 行 × 3 类 1 函数估算）
