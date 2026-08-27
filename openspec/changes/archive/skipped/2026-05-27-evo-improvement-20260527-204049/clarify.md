# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为无测试覆盖的核心模块 `zsiga/daemon.py`（1056 行、21 函数、1 类）新建 `tests/test_daemon.py`，重点覆盖 6 个高复杂度函数（CC>10），使用 mock 隔离外部依赖（LLM、文件 I/O、subprocess），不修改被测源码。

### 已有覆盖说明
项目中已存在 3 个 daemon 相关测试文件，但均非针对 `daemon.py` 的直接单元测试：
- `tests/test_daemon_cycle_resilience.py` — 循环韧性集成测试
- `tests/test_daemon_scheduling.py` — 调度策略测试
- `tests/test_daemon_state.py` — 状态读写测试（部分覆盖 `_read_daemon_state` / `_write_daemon_state`）

本 proposal 新建 `tests/test_daemon.py` 补充直接单元测试，不迁移或修改已有文件。

### 拆解后的子任务

- [ ] 1. **路径与状态工具函数测试** — 覆盖 `_lock_path`(L34)、`_daemon_state_path`(L42)、`_read_daemon_state`(L48)、`_write_daemon_state`(L59)。使用 tmpdir mock 文件系统，验证路径构造、JSON 序列化/反序列化、异常处理。 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 2. **文件锁管理测试** — 覆盖 `acquire_lock`(L94)、`release_lock`(L112)。验证锁文件创建/释放、fcntl 锁行为、异常路径（锁已被持有）。 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 3. **队列扫描逻辑测试** — 覆盖 `_scan_proposal_queue`(L122, CC=29, 90行)。构造不同状态 proposal 目录（pending/in-progress/completed/rejected）、损坏文件、空队列等场景，验证过滤、排序、状态转换逻辑。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)
- [ ] 4. **状态/指标构建器测试** — 覆盖 `_compute_uptime_seconds`(L214)、`_build_status_json`(L229)、`_build_metrics_json`(L249)。验证输出结构、字段完整性、边界值（启动时间为 0、超大 cycle 数）。 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 5. **Pipeline 状态详情构建测试** — 覆盖 `_build_pipeline_status`(L356, CC=32)、`_build_proposal_detail`(L529, CC=20)、`_build_evolution_status`(L638, CC=11)。Mock orchestrator/evolution 依赖，验证多状态分支覆盖。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)
- [ ] 6. **Dashboard HTTP handler 测试** — 覆盖 `_serve_dashboard.do_GET`(L726, CC=15)。验证路由分发（/status、/metrics、/dashboard）、响应格式。 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 7. **Daemon 主循环测试** — 覆盖 `daemon_loop`(L799, CC=38, 258行)。Mock 全部外部依赖，验证空闲循环、单次变更处理、连续忙碌、异常恢复等关键路径。不追求 100% 分支覆盖，聚焦 happy path + 关键 error path。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含至少 3 个 `def test_` 函数
- 必须包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个测试（BAC-02 要求）
- 优先覆盖 6 个高 CC 函数的关键分支
- 使用 mock/fixture 隔离文件系统、subprocess、LLM 调用

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（含不修复其 2 个 lint 问题：F401 unused import、F541 empty f-string）
- 不迁移或修改已有的 `test_daemon_*.py` 文件
- 不添加集成测试或端到端测试
- 不修改 `conftest.py` 或其他共享 fixture 文件

### 依赖的外部条件
- `zsiga/daemon.py` 在当前分支上存在且可导入
- `pytest` 和 `unittest.mock` 可用
- 项目已有 `tests/conftest_zsiga.py` 提供 sys.path 设置

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在
2. 文件中包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个函数
3. 文件中包含至少 3 个 `def test_` 函数
4. `python -m pytest tests/test_daemon.py` 退出码 0（所有测试通过）
5. 覆盖高 CC 函数（`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`）的关键分支

### 验收方式
- 文件存在性：`test -f tests/test_daemon.py`
- 符号存在性：`grep -c 'def test__lock_path\|def test__daemon_state_path\|def test__read_daemon_state' tests/test_daemon.py` ≥ 3
- 测试数量：`grep -c 'def test_' tests/test_daemon.py` ≥ 3
- 全部通过：`python -m pytest tests/test_daemon.py -v` 退出码 0
- Lint 通过：`ruff check tests/test_daemon.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 被测模块，只读
- `tests/test_daemon_cycle_resilience.py` — 已有测试，不触碰
- `tests/test_daemon_scheduling.py` — 已有测试，不触碰
- `tests/test_daemon_state.py` — 已有测试，不触碰
- `tests/conftest_zsiga.py` — 共享配置，不修改
- `pyproject.toml` / `requirements.txt` — 不新增依赖

### 项目部署分支
- main（默认分支）

### 已知风险
- **daemon_loop(CC=38) mock 复杂度极高**：该函数 258 行，涉及状态机、文件 I/O、subprocess、LLM 交互。完全覆盖不现实，应聚焦 happy path + 关键 error path，避免过度 mock 导致测试脆弱
- **已有 test_daemon_state.py 可能重复**：该文件已覆盖 `_read_daemon_state`/`_write_daemon_state` 的部分场景，新测试需避免简单重复，应补充边界值和异常路径
- **Import 路径依赖**：`daemon.py` 内部导入 `zsiga.pipeline.orchestrator` 等模块，mock 时需确保 import 链可解析
- **glob 未使用 import (F401)**：daemon.py L362 有未使用的 `glob` import，不影响测试但测试中不应触发该路径的副作用

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考（同类模块测试任务无精确记录，按每任务 ~2000-3000 token prompt + ~1000-1500 completion 估算，7 个任务合计）
