# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行, 21 函数, 1 类）新建 `tests/test_daemon.py`，覆盖尚未测试的公开函数和内部辅助函数。已有 3 个 daemon 测试文件（`test_daemon_state.py` 242L、`test_daemon_scheduling.py` 421L、`test_daemon_cycle_resilience.py` 213L）覆盖了 `_write_daemon_state`、`daemon_loop` 调度策略和错误恢复。本 proposal 补充覆盖其余未测函数。

### 拆解后的子任务

- [ ] 1. **路径工具函数测试** — `_lock_path()`, `_daemon_state_path()`, `_read_daemon_state()` (预估复杂度：低, 预估 token：~3000)
  - 文件范围：`tests/test_daemon.py` 新建，导入自 `zsiga.daemon`
  - `test__lock_path`：验证返回路径包含 `zsiga-daemon.pid`
  - `test__daemon_state_path`：验证返回路径包含 `daemon_state.json`
  - `test__read_daemon_state`：用 `tmp_path` 构造 JSON 文件，验证返回 dict；文件不存在时返回空 dict
  - 满足 BAC-02 / BAC-03 / BAC-04

- [ ] 2. **锁管理函数测试** — `acquire_lock()`, `release_lock(fd)` (预估复杂度：中, 预估 token：~4000)
  - 文件范围：`tests/test_daemon.py`
  - `acquire_lock`：mock `fcntl.flock`，验证成功时返回 fd 并写入 PID
  - `acquire_lock` 失败：模拟 `OSError`，验证异常传播
  - `release_lock`：mock fd close，验证锁释放流程
  - 需 mock：`fcntl`、`os.getpid`

- [ ] 3. **轻量构建器与工具函数测试** — `_compute_uptime_seconds()`, `_build_status_json()`, `_build_metrics_json()`, `DaemonState` 类, `_health_check()` (预估复杂度：中, 预估 token：~5000)
  - 文件范围：`tests/test_daemon.py`
  - `_compute_uptime_seconds`：传入过去时间戳，验证返回正整数秒；传入 None 验证返回 0
  - `_build_status_json`：mock `_read_daemon_state` 和全局状态，验证 JSON 结构包含 `state`/`pid`/`uptime_seconds` 字段
  - `_build_metrics_json`：验证返回结构包含 `cycles`/`changes` 等聚合字段
  - `DaemonState`：验证默认值 `paused=False`, `shutdown=False`，验证可变共享行为
  - `_health_check`：用 `tmp_path` 创建 SQLite 文件验证返回 True；传入不存在路径验证返回 False

- [ ] 4. **高复杂度构建器测试** — `_scan_proposal_queue()`, `_detect_proposal_phase()`, `_build_current_json()`, `_build_pipeline_status()`, `_build_proposal_detail()` (预估复杂度：高, 预估 token：~8000)
  - 文件范围：`tests/test_daemon.py`
  - `_scan_proposal_queue`：用 `tmp_path` 构造 `openspec/changes/` 目录树（含 proposal.md 的有效目录、空目录、无 proposal.md 的目录），验证过滤逻辑和返回结构
  - `_detect_proposal_phase`：构造含 `.phase_state` 文件的目录，验证阶段检测（CLARIFY/ENRICH/IMPLEMENT）
  - `_build_current_json`：mock `_scan_proposal_queue` 和 `_detect_proposal_phase`，验证返回的 JSON 包含 `active`/`queue` 字段
  - `_build_pipeline_status`：用 `tmp_path` + SQLite 构造 `changes` 表数据，验证 `phases_json` 解析和阶段进度计算
  - `_build_proposal_detail`：构造目录结构 + mock DB 读取，验证详情 JSON 结构

- [ ] 5. **统计与演进状态测试** — `_build_proposal_stats_json()`, `_build_budget_analysis_json()`, `_build_langfuse_summary()`, `_build_evolution_status()` (预估复杂度：中, 预估 token：~5000)
  - 文件范围：`tests/test_daemon.py`
  - `_build_proposal_stats_json`：mock DB 查询，验证统计聚合（总数/成功/失败/成功率）
  - `_build_budget_analysis_json`：验证预算分析 JSON 结构
  - `_build_langfuse_summary`：mock langfuse 读取，验证摘要格式
  - `_build_evolution_status`：mock `EvolutionState` 加载，验证 enabled/proposals_generated 等字段

- [ ] 6. **Dashboard HTTP 服务测试** — `_serve_dashboard()` (预估复杂度：高, 预估 token：~4000)
  - 文件范围：`tests/test_daemon.py`
  - 启动 HTTP 服务线程，用 `httpx` 发 GET 请求验证 `/api/status.json`、`/api/metrics.json` 路由返回有效 JSON
  - 验证静态文件路由 `site/dashboard.html` 返回 HTML
  - 验证未知路径返回 404
  - 需在独立端口运行，测试后关闭

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，覆盖 daemon.py 中未测函数
- 使用 mock 隔离外部依赖（fcntl、subprocess、asyncio、SQLite、文件系统）
- 遵循项目已有测试模式（`monkeypatch`、`tmp_path`、`@patch`、`TestXxx` 类分组）
- BAC 验收：文件存在 + 3 个指定测试函数 + pytest 退出码 0

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括 L362 的 unused import 和 L965 的 f-string 问题）
- 不修改已有测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）
- 不覆盖 `daemon_loop` 主循环（已在 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 中覆盖）
- 不覆盖 `_write_daemon_state`（已在 `test_daemon_state.py` 中覆盖）
- 不覆盖 dashboard 的队列 API（已在 `test_dashboard_queue.py` 中覆盖）

### 依赖的外部条件
- `zsiga/daemon.py` 当前接口不变（函数签名和模块结构稳定）
- 项目依赖中 `ruff`、`pytest` 可用
- `tests/conftest_zsiga.py` 中的共享 fixture 可用

## 目标

### 成功标准
1. `tests/test_daemon.py` 存在且包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个测试函数
2. 文件中 `def test_` 函数数量 ≥ 3（目标 ~25-35 个，覆盖上述 6 个功能模块）
3. `python -m pytest tests/test_daemon.py` 退出码 0，无 ruff lint 错误
4. 测试按功能域用 `TestXxx` 类分组，遵循项目约定

### 验收方式
- `test -f tests/test_daemon.py` 验证文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 3
- `grep -q 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state' tests/test_daemon.py` 验证 BAC-02
- `python -m pytest tests/test_daemon.py -v --tb=short` 验证全部通过
- `ruff check tests/test_daemon.py` 验证无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 只读分析
- `tests/test_daemon_state.py` — 已有覆盖
- `tests/test_daemon_scheduling.py` — 已有覆盖
- `tests/test_daemon_cycle_resilience.py` — 已有覆盖
- `tests/test_dashboard_api.py` — 已有覆盖
- `tests/test_dashboard_queue.py` — 已有覆盖

### 项目部署分支
- deploy

### 已知风险
- `_scan_proposal_queue` CC=29、`_build_pipeline_status` CC=32、`daemon_loop` CC=51 — 高复杂度函数 mock 隔离困难，测试可能遗漏分支路径；策略：优先覆盖主路径和边界条件，不强求 100% 分支覆盖
- `_serve_dashboard` 内嵌 `http.server.HTTPServer`，测试需启动真实 HTTP 服务线程，端口冲突风险；策略：使用 `0` 端口自动分配
- `fcntl` 在非 Unix 环境不可用，CI 兼容性风险；策略：`@patch("zsiga.daemon.fcntl")` 全量 mock
- 此 proposal 已被 pushback/skip 10+ 次，自演进循环风险；策略：严格限定范围为新建单文件，不修改任何现有代码

### 预估 token 消耗
- prompt: ~18000
- completion: ~12000
- 数据来源: 无历史参考（同类 proposal 无成功记录），基于测试代码行数估算（目标 ~400-600 行测试代码，按 1:20 token/行比）
