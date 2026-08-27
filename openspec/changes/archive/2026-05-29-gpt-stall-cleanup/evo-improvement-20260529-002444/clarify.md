# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1102 行, 21 函数, 1 类）创建 `tests/test_daemon.py` 单元测试文件。该模块已有 3 个侧面测试文件（`test_daemon_state.py` 242L、`test_daemon_scheduling.py` 421L、`test_daemon_cycle_resilience.py` 213L），但缺少直接覆盖高复杂度函数（CC>10）的测试。本次聚焦于未被现有测试覆盖的函数，避免与已有测试重复。

### 拆解后的子任务

- [ ] 1. **路径与状态工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`，使用 `monkeypatch` mock `os.path.expanduser` 和文件读取 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 2. **状态持久化与锁管理测试** — 覆盖 `_write_daemon_state()`（9 个参数）、`acquire_lock()`、`release_lock()`，使用 `tmp_path` + `fcntl.flock` mock (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 3. **提案队列扫描与状态构建测试** — 覆盖 `_scan_proposal_queue()`(CC=29, 90L)、`_compute_uptime_seconds()`、`_build_status_json()`、`_build_metrics_json()`，mock `os.listdir`、`json.load`、`time.time`、`config.load_config` (预估复杂度：高, 预估 token：~6000 / 无历史参考)
- [ ] 4. **Pipeline 状态与提案详情构建器测试** — 覆盖 `_build_pipeline_status()`(CC=32, 103L)、`_build_proposal_detail()`(CC=20, 76L)、`_build_evolution_status()`(CC=11, 64L)，mock `metrics.db.load_all_changes()`、文件系统读取 (预估复杂度：高, 预估 token：~6000 / 无历史参考)
- [ ] 5. **Dashboard 与主循环集成测试** — 覆盖 `_serve_dashboard.do_GET()`(CC=16)、`daemon_loop()`(CC=49) 的关键分支，mock `http.server`、`subprocess.run`、LLM 调用链路 (预估复杂度：高, 预估 token：~5000 / 无历史参考)

## 边界

### IN scope
- 创建 `tests/test_daemon.py`，包含对 `zsiga/daemon.py` 中 21 个函数的单元测试
- 优先覆盖 6 个高 CC 函数（CC>10）的关键分支
- 使用 mock/monkeypatch 隔离外部依赖（文件 I/O、subprocess、LLM 调用、config 加载）
- 每个测试可独立运行，不依赖运行时环境或网络

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复 2 个 lint 问题：L362 F401 unused glob、L965 F541 empty f-string）
- 不修改已有测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）
- 不与已有测试重复覆盖（`_write_daemon_state`、`_read_daemon_state` 在 `test_daemon_state.py` 已有 10+ 用例，本次仅补充未覆盖分支）
- 不涉及其他模块的测试

### 依赖的外部条件
- `zsiga/daemon.py` 源码在当前分支上稳定可用
- 项目 `conftest_zsiga.py` fixture 可引用
- `pytest` + `unittest.mock` + `monkeypatch` 可用
- `ruff` 用于 lint 检查

## 目标

### 成功标准
1. `tests/test_daemon.py` 存在且包含至少 15 个 `def test_` 函数（覆盖 21 个函数中的主要公开/可测函数）
2. 包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个基础函数测试
3. 至少覆盖 3 个高 CC 函数（`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`）的关键分支
4. `python -m pytest tests/test_daemon.py` 退出码 0，无失败/错误
5. `ruff check tests/test_daemon.py` 无错误

### 验收方式
- `test -f tests/test_daemon.py` 验证文件存在
- `grep -c 'def test_' tests/test_daemon.py` 验证测试函数数量 ≥ 15
- `grep -E 'def test__lock_path|def test__daemon_state_path|def test__read_daemon_state' tests/test_daemon.py` 验证 BAC-02 函数名
- `python -m pytest tests/test_daemon.py -v` 验证全部通过
- `ruff check tests/test_daemon.py` 验证无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析，不做任何修改
- `tests/test_daemon_state.py` — 已有覆盖，不重复
- `tests/test_daemon_scheduling.py` — 已有覆盖，不重复
- `tests/test_daemon_cycle_resilience.py` — 已有覆盖，不重复
- `tests/conftest_zsiga.py` — 共享 fixture，不修改

### 项目部署分支
- 目标分支：当前分支（由 pipeline 自动确定）

### 已知风险
- **`daemon_loop` CC=49 极高复杂度**：301 行主循环函数，内嵌 LLM 调用链、subprocess、文件 I/O、异常处理，mock 链路长且脆弱，可能导致测试维护成本高
- **已有侧面测试重叠**：`_write_daemon_state` 和 `_read_daemon_state` 已在 `test_daemon_state.py` 中有 10+ 用例，需避免重复覆盖同一分支
- **proposal 历史失败率高**：此 proposal 已被 pushback 9 次、执行失败 1 次（MAX_TURNS_REACHED），主要原因是 BAC 过于宽松和复杂度估算不足
- **mock 深度**：`_build_pipeline_status` 依赖 `metrics.db.load_all_changes()` 返回 SQLite 查询结果，mock 数据结构需精确匹配源码预期

### 预估 token 消耗
- prompt: ~15000
- completion: ~8000
- 数据来源: 无历史参考（同类 proposal 从未成功完成执行阶段）
