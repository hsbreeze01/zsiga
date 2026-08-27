# add-tests-daemon

## Summary
为无测试模块 `zsiga/daemon.py` (1110 行, 21 函数, 1 类) 添加单元测试覆盖。

## Problem
模块 `zsiga/daemon.py` 缺少测试文件 `tests/test_daemon.py`，是潜在风险点。

### 当前状态（静态分析数据）
- 总行数: 1110
- 函数数: 21，类数: 1
- ruff lint 问题: 2
- 圈复杂度: 平均 7.5，高 CC(>10) 函数 6 个

### 函数列表
- `_lock_path()` L34-L39 (~6L)
- `_daemon_state_path()` L42-L45 (~4L)
- `_read_daemon_state()` L48-L56 (~9L)
- `_write_daemon_state(started_at, cycle, state, current_change, current_phase, current_project, total_cycles, total_changes_processed, idle_cycles, continuous_busy_cycles, last_change_at)` L59-L91 (~33L)
- `acquire_lock()` L94-L109 (~16L)
- `release_lock(fd)` L112-L119 (~8L)
- `_scan_proposal_queue(changes_dir)` L122-L211 (~90L)
- `_compute_uptime_seconds(started_at)` L214-L226 (~13L)
- `_build_status_json()` L229-L244 (~16L)
- `_build_metrics_json()` L249-L262 (~14L)

### 类结构
- `DaemonState` L28-L31 methods=[]

### Lint 问题
- L362 [F401]: `glob` imported but unused
- L965 [F541]: f-string without any placeholders

### 高复杂度函数 (CC > 10)
- `_scan_proposal_queue` L122 CC=29 (90L)
- `_build_pipeline_status` L356 CC=32 (103L)
- `_build_proposal_detail` L529 CC=20 (76L)
- `_build_evolution_status` L638 CC=11 (64L)
- `_serve_dashboard.do_GET` L726 CC=16 (67L)
- `daemon_loop` L802 CC=51 (309L)

## Technical Design
1. 为 `zsiga/daemon.py` 中的公开函数编写单元测试
2. 优先覆盖高复杂度函数: `_scan_proposal_queue`, `_build_pipeline_status`, `_build_proposal_detail`
3. 使用 mock 隔离外部依赖（LLM 调用、文件 I/O、subprocess）
4. 确保每个测试可独立运行，不依赖运行时环境

### Target Files
- `tests/test_daemon.py` (新建)
- `zsiga/daemon.py` (仅读取分析，不修改)

## Acceptance Criteria
- [BAC-01] 文件 `tests/test_daemon.py` 存在
- [BAC-02] `tests/test_daemon.py` 中存在 `test__lock_path`, `test__daemon_state_path`, `test__read_daemon_state`
- [BAC-03] `tests/test_daemon.py` 中存在至少 3 个 `def test_` 函数
- [BAC-04] `python -m pytest tests/test_daemon.py` 退出码 0

## Scope
- In scope: 为 `zsiga/daemon.py` 编写测试，覆盖公开函数
- Out of scope: 不修改 `zsiga/daemon.py` 源码

## Risk
- Impact: None — 只添加测试
- Reversibility: 删除测试文件

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（含静态分析数据）
- project=zsiga
