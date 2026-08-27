# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行, 21 函数, 1 类）新建 `tests/test_daemon.py`，补充现有 3 个测试文件未覆盖的函数单元测试。

**已有测试覆盖（22 个测试，3 个文件）**：
- `tests/test_daemon_state.py`（10 测试）— `_write_daemon_state` 字段写入、null 处理、心跳更新、统计持久化
- `tests/test_daemon_cycle_resilience.py`（5 测试）— daemon 错误恢复
- `tests/test_daemon_scheduling.py`（7 测试）— 自适应调度策略

**真正缺失直接单元测试的函数**：`_lock_path`, `_daemon_state_path`, `_read_daemon_state`, `acquire_lock`, `release_lock`, `_scan_proposal_queue`, `_build_status_json`, `_build_metrics_json`, `_compute_uptime_seconds`, `_health_check`, `_build_proposal_stats_json`, `_build_budget_analysis_json`, `_build_langfuse_summary`, `_detect_proposal_phase`, `_build_current_json`

**高复杂度函数（CC > 10，测试价值最高）**：
- `_scan_proposal_queue` (CC=29, 90L) — proposal 队列扫描
- `_build_pipeline_status` (CC=32, 103L) — pipeline 状态构建
- `_build_proposal_detail` (CC=20, 76L) — proposal 详情构建
- `daemon_loop` (CC=51, 309L) — 主循环（极难测试，需大量 mock）

### 拆解后的子任务

- [ ] 1. 路径与状态读写函数测试：`_lock_path`, `_daemon_state_path`, `_read_daemon_state`, `_compute_uptime_seconds`（预估复杂度：低, 预估 token：~2000 / 无历史参考）
  - 验证路径生成逻辑（受 `ZSIGA_HOME` 环境变量影响）
  - 验证 `_read_daemon_state` 对缺失文件/空文件/合法 JSON 的处理
  - 验证 `_compute_uptime_seconds` 对各种时间输入的计算
  - 范围：`tests/test_daemon.py` 新建

- [ ] 2. 文件锁函数测试：`acquire_lock`, `release_lock`（预估复杂度：中, 预估 token：~2500 / 无历史参考）
  - 使用 `tmp_path` 隔离文件系统，不污染项目 `data/` 目录
  - 验证排他锁获取/释放、重复锁定行为、锁文件创建
  - 范围：`tests/test_daemon.py`

- [ ] 3. Proposal 队列扫描测试：`_scan_proposal_queue`（预估复杂度：高, 预估 token：~4000 / 无历史参考）
  - CC=29，需构造多种 proposal 目录结构（waiting/completed/paused/stuck/active）
  - 使用 `tmp_path` 构造 changes_dir，模拟 `.paused` 文件、`.phase_state` 文件
  - 验证各 lifecycle 状态的判定逻辑、consecutive_fails 统计
  - 范围：`tests/test_daemon.py`

- [ ] 4. JSON 构建函数测试：`_build_status_json`, `_build_metrics_json`, `_build_current_json`（预估复杂度：中, 预估 token：~2500 / 无历史参考）
  - Mock `_read_daemon_state` 返回值，验证输出 JSON 结构
  - 验证边界情况（空状态、缺失字段）
  - 范围：`tests/test_daemon.py`

- [ ] 5. Lint 与 pytest 验证（预估复杂度：低, 预估 token：~500 / 无历史参考）
  - `ruff check tests/test_daemon.py` 通过
  - `python -m pytest tests/test_daemon.py` 退出码 0
  - 确保与现有 3 个 daemon 测试文件无冲突：`python -m pytest tests/test_daemon*.py` 退出码 0
  - 范围：`tests/test_daemon.py`

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，覆盖 `_lock_path`, `_daemon_state_path`, `_read_daemon_state`, `acquire_lock`, `release_lock`, `_scan_proposal_queue`, `_build_status_json`, `_build_metrics_json`, `_compute_uptime_seconds` 等函数
- 使用 `tmp_path` / `monkeypatch` 隔离文件系统和环境变量
- 使用 `unittest.mock` 隔离外部依赖（LLM 调用、subprocess、SQLite）
- BAC 验收：文件存在、包含指定测试函数名、pytest 通过

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复 2 个 ruff lint 问题：L362 F401, L965 F541）
- 不覆盖 `daemon_loop`（CC=51, 309 行主循环，集成级别，需 mock 整个 pipeline）
- 不覆盖 `_build_pipeline_status`（CC=32）和 `_build_proposal_detail`（CC=20）— 这两个函数依赖 SQLite `changes` 表，mock 成本极高，可在后续迭代中补充
- 不覆盖 `_serve_dashboard.do_GET`（HTTP handler，需要集成测试框架如 `httpx.ASGITransport`）
- 不覆盖 `_build_evolution_status`（依赖 langfuse 等外部服务）
- 不修改现有 `tests/test_daemon_state.py`, `tests/test_daemon_cycle_resilience.py`, `tests/test_daemon_scheduling.py`
- 不覆盖已有测试已充分覆盖的 `_write_daemon_state`（10 个测试已存在）

### 依赖的外部条件
- `zsiga/daemon.py` 文件结构在实施期间不变更
- `pytest` + `unittest.mock` + `tmp_path` fixture 可用
- 项目 Python ≥3.10 环境可用
- 无外部网络/LLM 调用（全部 mock）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且通过 ruff check
2. 包含至少以下测试函数：`test__lock_path`, `test__daemon_state_path`, `test__read_daemon_state`, `test_acquire_lock`, `test_release_lock`, `test__scan_proposal_queue`
3. 测试总数 ≥ 10 个 `def test_` 函数
4. `python -m pytest tests/test_daemon.py -v` 退出码 0，所有测试通过
5. `python -m pytest tests/test_daemon_state.py tests/test_daemon_cycle_resilience.py tests/test_daemon_scheduling.py tests/test_daemon.py` 全部通过，无冲突

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 10
- `grep -q 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state\|test_acquire_lock\|test_release_lock\|test__scan_proposal_queue' tests/test_daemon.py` 确认关键函数存在
- `python -m pytest tests/test_daemon.py` 退出码 0
- `ruff check tests/test_daemon.py` 无错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 只添加测试，不修改源码
- `tests/test_daemon_state.py` — 已有 10 个测试覆盖 `_write_daemon_state`
- `tests/test_daemon_cycle_resilience.py` — 已有 5 个测试
- `tests/test_daemon_scheduling.py` — 已有 7 个测试
- `tests/conftest_zsiga.py` — 全局 conftest 不动
- `pyproject.toml`, `requirements.txt` — 不添加新依赖

### 项目部署分支
`deploy`

### 已知风险
- **历史失败率极高**：此 proposal 已被 SKIP/PUSHBACK 10+ 次，从未成功交付。自演进引擎在 `tests/__pycache__/` 中留下了 60+ 个失败尝试的 `.pyc` 文件
- **`_scan_proposal_queue` mock 复杂度高**：CC=29，需构造多种 proposal 目录结构和 `.phase_state` JSON 文件，测试用例设计可能耗时较长
- **daemon.py 内部耦合**：多个 `_build_*` 函数依赖 `_read_daemon_state()` 和 SQLite，需仔细 mock 依赖链
- **函数签名可能变更**：daemon.py 是活跃开发模块，函数签名可能在实施期间变更
- **import 路径**：需确认 `from zsiga.daemon import _lock_path` 等私有函数是否可直接导入（Python 不阻止，但需确认 `__all__` 无限制）

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考（同类任务从未成功交付）
