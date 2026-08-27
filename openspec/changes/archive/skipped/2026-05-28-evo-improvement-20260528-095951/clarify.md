# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1077 行，21 函数，1 类）新建 `tests/test_daemon.py`，补充单元测试覆盖。已有 3 个 daemon 测试文件（`test_daemon_state.py` 242L/10 tests、`test_daemon_scheduling.py` 421L/9 tests、`test_daemon_cycle_resilience.py` 213L/6 tests）覆盖了 `_write_daemon_state`、`_read_daemon_state`（间接）、`daemon_loop` 调度/恢复。本 proposal 旨在覆盖**尚未被直接测试的函数**，优先高复杂度目标。

### 拆解后的子任务

- [ ] 1. **路径工具与状态读取测试** — `_lock_path`、`_daemon_state_path`、`_read_daemon_state`（直接测试，现有文件仅间接覆盖后者）。覆盖：路径拼接正确性、文件不存在返回默认 dict、损坏 JSON 处理。（预估复杂度：低, 预估 token：~3000）
- [ ] 2. **锁管理测试** — `acquire_lock`、`release_lock`。覆盖：锁文件创建、fd 返回值非 None、release 关闭 fd、锁文件清理。（预估复杂度：低, 预估 token：~2500）
- [ ] 3. **Proposal 队列扫描测试** — `_scan_proposal_queue`（CC=29，90 行）。覆盖：空目录返回空列表、正常 proposal 提取 name/project/summary/phase/lifecycle、缺少 proposal.md 跳过、损坏 JSON 跳过、consecutive_fails 计数、paused 状态解析。需 mock `load_config`、`os.listdir`、文件读取。（预估复杂度：高, 预估 token：~6000）
- [ ] 4. **运行时间与状态 JSON 测试** — `_compute_uptime_seconds`、`_build_status_json`。覆盖：有效 started_at 返回正整数、无效时间返回 0、`_build_status_json` 返回含 `state`/`cycle`/`uptime_seconds` 键的 dict。需 mock `_read_daemon_state` 和 `_compute_uptime_seconds`。（预估复杂度：中, 预估 token：~3500）
- [ ] 5. **指标与 Pipeline 状态测试** — `_build_metrics_json`、`_build_pipeline_status`（CC=32）。覆盖：`_build_metrics_json` 返回含 `proposals`/`success_rate`/`uptime` 结构；`_build_pipeline_status` 有活跃 proposal 时返回含 `current`/`queue` 的结构、无活跃 proposal 时 current 为 None。需 mock `_read_daemon_state`、`_scan_proposal_queue`、`db` 模块。（预估复杂度：高, 预估 token：~5500）
- [ ] 6. **Proposal 详情构建测试** — `_build_proposal_detail`（CC=20）。覆盖：正常 proposal 返回含 `name`/`project`/`phases`/`history` 结构、phase_state 文件缺失时降级、db_record 缺失时降级。需 mock 文件系统和 db 查询。（预估复杂度：高, 预估 token：~5000）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含上述 6 组测试
- 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`、`_build_proposal_detail` 共 11 个函数
- 使用 `monkeypatch` + `tmp_path` + `unittest.mock` 隔离外部依赖
- 所有测试可独立运行，不依赖运行时 daemon 状态

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（含 L362 F401 `glob` unused import、L940 F541 f-string 问题 — 属于 lint 修复范畴）
- 不测试 `daemon_loop`（CC=43，276 行）— 已在 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 中覆盖
- 不测试 `_serve_dashboard.do_GET`（CC=16）— HTTP handler，属于集成测试范畴
- 不测试 `_build_evolution_status`（CC=11）— 依赖 EvolutionEngine 完整初始化，mock 链过长
- 不重复 `test_daemon_state.py` 中已有的 `_write_daemon_state` 直接测试
- 不修改已有的 3 个 daemon 测试文件

### 依赖的外部条件
- `zsiga/daemon.py` 可正常 import（无循环依赖）
- `zsiga/metrics/db.py` 可 import（`_DB_PATH`、`load_all_changes`）
- `zsiga/config.py` 可 import（`load_config`）
- pytest + pytest-mock 可用（项目已有 `conftest_zsiga.py`）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥ 15 个 `def test_` 函数
2. 覆盖上述 11 个目标函数中的至少 9 个（`_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`）
3. `python -m pytest tests/test_daemon.py` 退出码 0，无 skip
4. 不与已有 3 个 daemon 测试文件产生功能重复（`_write_daemon_state` 不在新文件中测试）
5. 所有 mock 使用 `monkeypatch` 或 `unittest.mock.patch`，不依赖真实文件系统/网络

### 验收方式
- `test -f tests/test_daemon.py`（BAC-01）
- `grep -c 'def test_' tests/test_daemon.py` ≥ 15
- `grep -q 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state' tests/test_daemon.py`（BAC-02）
- `python -m pytest tests/test_daemon.py -v --tb=short` 退出码 0（BAC-04）
- `ruff check tests/test_daemon.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 只读取分析，不做任何修改
- `tests/test_daemon_state.py` — 已有覆盖，不扩展
- `tests/test_daemon_scheduling.py` — 已有覆盖，不扩展
- `tests/test_daemon_cycle_resilience.py` — 已有覆盖，不扩展
- `tests/conftest_zsiga.py` — 不修改项目级 fixture

### 项目部署分支
- `main`

### 已知风险
- **已有测试重叠**：`_read_daemon_state` 在 `test_daemon_state.py` 中被间接测试（通过 `_write_daemon_state` round-trip），新文件需提供**独立**的直接测试（如损坏 JSON、文件不存在等边界场景），避免重复
- **高 CC 函数 mock 链长**：`_build_pipeline_status`（CC=32）需 mock `_read_daemon_state` + `_scan_proposal_queue` + `db.load_all_changes` + 文件系统，setup 复杂度高
- **daemon 模块内部耦合**：`_build_proposal_detail` 依赖 `.phase_state` 文件 + SQLite 查询，mock 需精确控制文件存在性和 db 返回值
- **BAC 门槛极低**：原始 BAC 仅要求 3 个 test_ 函数，需执行者自觉覆盖更多函数以达到实质价值

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考（基于 6 个子任务复杂度加总估算）
