# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行, 21 函数, 1 类）中尚未被现有 3 个测试文件覆盖的函数，新建 `tests/test_daemon.py` 编写单元测试。现有覆盖：`tests/test_daemon_state.py`（`_write_daemon_state`）、`tests/test_daemon_scheduling.py`（`daemon_loop` 调度）、`tests/test_daemon_cycle_resilience.py`（cycle 容错）。本次重点覆盖高 CC 函数：`_scan_proposal_queue`(CC=29)、`_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20)。

### 拆解后的子任务
- [ ] 1. **路径/状态工具函数测试** — `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`_compute_uptime_seconds`、`DaemonState` dataclass、`acquire_lock`/`release_lock`（预估复杂度：低, 预估 token：~2500 / 无历史参考）
- [ ] 2. **`_scan_proposal_queue` 测试** — 文件系统扫描、状态分类逻辑（new/enrich/implement/verify/fix/done/skip/reject）、排序策略、边界场景（空目录/无元数据）（预估复杂度：高, 预估 token：~4000 / 无历史参考）
- [ ] 3. **状态构建器测试** — `_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`、`_build_proposal_detail`、`_build_evolution_status`，需 mock daemon state 和 changes 目录（预估复杂度：中, 预估 token：~3500 / 无历史参考）
- [ ] 4. **Dashboard handler 测试** — `_serve_dashboard.do_GET` HTTP 路由与响应格式验证，需 mock socket/server（预估复杂度：中, 预估 token：~3000 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`
- 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`_compute_uptime_seconds`、`DaemonState`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`、`_build_proposal_detail`、`_build_evolution_status`、`_serve_dashboard.do_GET`
- 使用 `tmp_path`/`monkeypatch` 隔离文件系统，`unittest.mock` 隔离外部依赖

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（含 2 个已知 lint 问题 L362 F401、L965 F541）
- 不覆盖 `daemon_loop`（CC=51，已被 `test_daemon_scheduling.py` 覆盖）
- 不覆盖 `_write_daemon_state`（已被 `test_daemon_state.py` 覆盖）
- 不修改现有 3 个测试文件

### 依赖的外部条件
- `zsiga/daemon.py` 当前接口签名稳定（函数名、参数不变）
- 现有 `tests/test_daemon_state.py` 等 3 文件提供 mock 惯例参考（`monkeypatch.setattr("zsiga.daemon._daemon_state_path", ...)`）

## 目标

### 成功标准
1. `tests/test_daemon.py` 存在且包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个测试函数
2. 文件内包含 ≥3 个 `def test_` 函数
3. `python -m pytest tests/test_daemon.py` 退出码 0
4. 新测试不破坏现有测试套件（`python -m pytest tests/` 退出码 0）

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` ≥ 3
- `grep -q 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state' tests/test_daemon.py`
- `python -m pytest tests/test_daemon.py -x -q` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（仅读取分析）
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`

### 项目部署分支
- deploy

### 已知风险
- `_build_pipeline_status`(CC=32) 和 `_scan_proposal_queue`(CC=29) 分支密集，mock 链可能较长，测试可读性需注意
- `_serve_dashboard` 是 `BaseHTTPRequestHandler` 子类的内部类方法，构造测试实例需 mock socket/address/server 等参数
- 此 proposal 曾被 PUSHBACK ≥15 次，需确保 BAC 验收标准可实际达成，避免再次空转

### 预估 token 消耗
- prompt: ~3000
- completion: ~5000
- 数据来源: 无历史参考（同类任务无成功执行记录）
