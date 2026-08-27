# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行, 21 函数, 1 类）新建 `tests/test_daemon.py`，提供单元测试覆盖。当前虽有 4 个 daemon 相关测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`、`test_dashboard_api.py`），但它们分散覆盖了部分函数，核心模块 `daemon.py` 本身缺少直接测试文件。

### 拆解后的子任务

- [ ] 1. **工具函数与锁管理层** — 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_compute_uptime_seconds` 6 个低复杂度函数。使用 `monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))` 隔离文件系统，`unittest.mock.patch("zsiga.daemon.fcntl.flock")` 隔离系统调用。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 2. **状态构建与指标层** — 覆盖 `_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`（CC=32）、`_build_proposal_detail`（CC=20）、`_build_evolution_status`（CC=11）。需要 mock `metrics.db` / `metrics.dashboard` / `metrics.budget_analyzer` 模块依赖和 SQL 查询。（预估复杂度：中, 预估 token：~5000 / 无历史参考）
- [ ] 3. **队列扫描与 Dashboard HTTP 层** — 覆盖 `_scan_proposal_queue`（CC=29, 90L）和 `_serve_dashboard.do_GET`（CC=16, 67L）。需要构造目录结构 fixture、mock HTTP 请求响应、隔离 `load_all_changes`。（预估复杂度：中, 预估 token：~5000 / 无历史参考）
- [ ] 4. **daemon_loop 主循环** — 覆盖 `daemon_loop`（CC=51, 309L）的核心路径：正常 cycle、idle 跳过、shutdown 信号、异常处理。需要 mock `time.sleep`、`_scan_proposal_queue`、pipeline 调用链等大量依赖，通过有限 cycle 数控制测试终止。（预估复杂度：高, 预估 token：~6000 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，覆盖 `zsiga/daemon.py` 中的公开/内部函数
- 使用 monkeypatch、tmp_path、unittest.mock 隔离外部依赖
- 遵循项目已有测试模式（参考 `test_daemon_state.py`、`test_daemon_scheduling.py` 的 fixture/mock 风格）
- BAC 要求的最低 3 个 `test_` 函数（`test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state`）

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括 2 个 lint 问题 L362 F401 和 L965 F541）
- 不修改已有的 4 个 daemon 相关测试文件
- 不测试 `DaemonState` 类的信号处理行为（依赖 OS 信号，集成测试范畴）
- 不修改 `zsiga/metrics/`、`zsiga/pipeline/` 等外部模块
- 不创建额外的 conftest 或 fixture 文件

### 依赖的外部条件
- `zsiga/daemon.py` 当前接口稳定，函数签名不发生破坏性变更
- pytest + monkeypatch + tmp_path + unittest.mock 可用（项目已有先例）
- `fcntl` 模块可通过 mock 替代（测试环境可能无真实文件锁）
- 已有 archive 中的参考实现（`skipped/2026-05-30-evo-improvement-20260530-085023/` 下 272 行版本，覆盖 8 个函数）可作为模式参考

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且通过 `python -m pytest tests/test_daemon.py`（退出码 0）
2. 包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个 BAC 要求的测试函数
3. 至少覆盖 8 个函数（含 BAC 最低 3 个 + 额外 5 个中高复杂度函数），总测试函数数 ≥ 12
4. 不引入新的 ruff lint 问题
5. 不破坏现有测试套件（`python -m pytest tests/` 整体通过）

### 验收方式
- `python -m pytest tests/test_daemon.py -v` 逐条列出通过/失败
- `python -m ruff check tests/test_daemon.py` 无 lint 错误
- `grep -c "def test_" tests/test_daemon.py` 计数 ≥ 12
- BAC-01~04 全部通过

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（只读分析）
- `tests/test_daemon_state.py`、`tests/test_daemon_scheduling.py`、`tests/test_daemon_cycle_resilience.py`、`tests/test_dashboard_api.py`（已有测试不动）
- `tests/conftest.py` 或 `tests/conftest_zsiga.py`（不新增全局 fixture）
- `zsiga/metrics/`、`zsiga/pipeline/`、`zsiga/config.py` 等外部模块

### 项目部署分支
deploy

### 已知风险
- **历史循环风险**：此 proposal 已被自演进引擎生成 24+ 次，全部在 gate/steward 阶段被拦截，本次是首次进入 clarify 阶段。需确保需求契约质量足够高以打破循环。
- **高复杂度函数 mock 难度**：`daemon_loop`（CC=51）和 `_build_pipeline_status`（CC=32）的 mock 链路极长，可能需要多轮迭代才能找到正确的隔离策略。
- **已有测试重叠**：`test_daemon_state.py` 已覆盖 `_write_daemon_state` 的 7 个场景，需避免重复测试同一函数。新文件应聚焦于未覆盖的函数。
- **`fcntl` 平台依赖**：`acquire_lock`/`release_lock` 依赖 `fcntl.flock`（仅 Unix），测试需 mock 该系统调用。

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类 proposal 从未进入执行阶段）
