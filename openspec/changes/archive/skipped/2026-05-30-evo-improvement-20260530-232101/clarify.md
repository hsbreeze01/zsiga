# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行，21 函数，1 类）新建 `tests/test_daemon.py`，补充未覆盖函数的单元测试。已有 5 个 daemon 相关测试文件（48 个测试函数），但聚焦于 `_write_daemon_state`、`daemon_loop` 调度/韧性、`_scan_proposal_queue`（dashboard 视角）和 `_build_status_json`，存在大量函数无直接覆盖。

### 拆解后的子任务

- [ ] 1. 路径与状态工具函数测试组 — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`、`_compute_uptime_seconds(started_at)` (预估复杂度：低, 预估 token：~4000 / 无历史参考)
  - 文件范围：`tests/test_daemon.py` 新建，导入 `zsiga.daemon`
  - 这些是纯路径拼接或简单读取函数，无需重度 mock
  - 用 `monkeypatch` 隔离文件系统路径，用 `tmp_path` 提供隔离目录

- [ ] 2. 文件锁操作测试组 — 覆盖 `acquire_lock()` 和 `release_lock(fd)` (预估复杂度：中, 预估 token：~5000 / 无历史参考)
  - 文件范围：`tests/test_daemon.py`
  - 需验证锁文件创建、独占获取、fd 正确关闭/释放
  - 用 `tmp_path` 隔离，避免污染真实 `_lock_path`

- [ ] 3. 高 CC JSON 构建函数测试组 — 覆盖 `_build_pipeline_status(cc=32)`、`_build_proposal_detail(cc=20)`、`_build_evolution_status(cc=11)`、`_build_metrics_json()` (预估复杂度：高, 预估 token：~12000 / 无历史参考)
  - 文件范围：`tests/test_daemon.py`
  - 这 4 个函数从全局/文件系统状态构建 JSON 结构，需 mock `daemon_state` 读取和目录结构
  - `_build_pipeline_status`（CC=32）需覆盖多分支：change 各 phase 状态、文件存在性检查、phase durations 计算
  - `_build_proposal_detail`（CC=20）需覆盖 proposal 目录中各文件解析分支
  - `_build_evolution_status`（CC=11）需覆盖 evolution state 读取和字段提取
  - `_build_metrics_json` 需验证 JSON 结构完整性

- [ ] 4. `_scan_proposal_queue` 深度覆盖测试组 — 补充已有 dashboard 测试未覆盖的分支路径 (预估复杂度：中, 预估 token：~6000 / 无历史参考)
  - 文件范围：`tests/test_daemon.py`
  - 已有 `test_dashboard_queue.py` 覆盖了 `_render_proposal_queue`（调用 `_scan_proposal_queue`），但非直接单元测试
  - 需直接测试：空队列、多 change 目录、不同 phase 状态、proposal.md 缺失、非法目录名

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含上述 4 组测试
- 覆盖以下未测试函数：`_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`_compute_uptime_seconds`、`acquire_lock`、`release_lock`、`_build_pipeline_status`、`_build_proposal_detail`、`_build_evolution_status`、`_build_metrics_json`
- 对 `_scan_proposal_queue` 补充直接单元测试（区别于已有集成测试）

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（含 2 个 ruff lint 问题：L362 F401、L965 F541）
- 不覆盖 `daemon_loop`（CC=51，已有 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 覆盖）
- 不覆盖 `_write_daemon_state`（已有 `test_daemon_state.py` 完整覆盖 10 个测试）
- 不覆盖 `_serve_dashboard.do_GET`（嵌套类方法，需 HTTP server mock，优先级低）
- 不修改或与已有 5 个 daemon 测试文件产生 fixture/import 冲突

### 依赖的外部条件
- pytest 和 monkeypatch/tmp_path fixture 可用（项目已使用 pytest）
- `zsiga/daemon.py` 可正常导入且无运行时 side effect（模块级代码不触发 daemon 启动）
- 现有 `preserve_daemon_state` fixture 模式（来自 `test_dashboard_api.py`）可参考但不应产生 fixture 名冲突

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥ 15 个 `def test_` 函数
2. 文件中包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个函数名
3. 高 CC 函数 `_build_pipeline_status`、`_build_proposal_detail`、`_scan_proposal_queue` 各有 ≥ 2 个针对性测试
4. `python -m pytest tests/test_daemon.py` 退出码 0，无 skip/error
5. 不与现有 `test_daemon_state.py`、`test_daemon_cycle_resilience.py`、`test_daemon_scheduling.py`、`test_dashboard_api.py`、`test_dashboard_queue.py` 产生 import 冲突或 fixture 碰撞

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 确认测试函数数量 ≥ 15
- `grep -E 'test__lock_path|test__daemon_state_path|test__read_daemon_state' tests/test_daemon.py` 确认指定函数存在
- `python -m pytest tests/test_daemon.py -v --tb=short` 确认全部通过
- `python -m pytest tests/test_daemon_state.py tests/test_daemon_cycle_resilience.py tests/test_daemon_scheduling.py tests/test_dashboard_api.py tests/test_dashboard_queue.py -v` 确认已有测试不受影响

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 只读分析
- `tests/test_daemon_state.py` — 已有测试，不碰
- `tests/test_daemon_cycle_resilience.py` — 已有测试，不碰
- `tests/test_daemon_scheduling.py` — 已有测试，不碰
- `tests/test_dashboard_api.py` — 已有测试，不碰
- `tests/test_dashboard_queue.py` — 已有测试，不碰
- `tests/conftest_zsiga.py` — 全局 conftest，不碰

### 项目部署分支
- deploy

### 已知风险
- **24+ 轮循环未打破**：此 proposal 历史版本全部在 gate/steward 阶段被拦截，无成功执行记录。本次需严格遵循已有测试模式（`monkeypatch` + `tmp_path` + `patch`），避免引入新 fixture 或 conftest 依赖
- **daemon_loop CC=51 不在本 scope**：主循环函数复杂度极高，强行覆盖会消耗大量 token 且收益低，已有 2 个专门测试文件覆盖调度和韧性
- **`_build_pipeline_status` CC=32**：多分支函数，需仔细构造测试数据覆盖关键路径，避免过度 mock 导致测试脆弱
- **全局状态隔离**：daemon 模块可能读取全局文件路径（`data/daemon_state.json`、`data/evolution_state.json`），每个测试必须用 `monkeypatch` 重定向到 `tmp_path`

### 预估 token 消耗
- prompt: ~18000
- completion: ~8000
- 数据来源: 无历史参考（同类 proposal 从未成功执行）
