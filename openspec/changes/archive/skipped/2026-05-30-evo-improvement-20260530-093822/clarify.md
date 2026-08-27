# clarify.md — add-tests-daemon

## 需求拆解
### 原始需求
为 `zsiga/daemon.py`（1110 行, 21 函数, 1 类）创建 `tests/test_daemon.py`，通过 mock 隔离外部依赖（文件 I/O、subprocess、LLM 调用），覆盖当前 3 个已有测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）未直接覆盖的函数。优先覆盖 6 个高复杂度函数（CC > 10）。

### 拆解后的子任务
- [ ] 1. **工具函数与状态持久化层测试** — 覆盖 `_lock_path`、`_daemon_state_path`、`_compute_uptime_seconds`、`_read_daemon_state`、`_write_daemon_state`、`DaemonState` 类（预估复杂度：低, 预估 token：~4000 / 无历史参考）
- [ ] 2. **锁管理测试** — 覆盖 `acquire_lock`、`release_lock`，mock 文件系统操作，验证锁文件创建/释放/异常路径（预估复杂度：中, 预估 token：~3000 / 无历史参考）
- [ ] 3. **队列扫描测试** — 覆盖 `_scan_proposal_queue`（CC=29），构造多种 proposal 目录结构（空队列/正常/含 .phase_state/含 consecutive_fails/已暂停），验证返回字段（name, project, summary, phase, lifecycle, paused 等）（预估复杂度：高, 预估 token：~5000 / 无历史参考）
- [ ] 4. **状态/指标响应构建测试** — 覆盖 `_build_status_json`、`_build_metrics_json`、`_build_current_json`、`_health_check`，mock `_read_daemon_state` 与 DB 查询，验证返回 JSON 结构（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 5. **Pipeline 状态构建测试** — 覆盖 `_build_pipeline_status`（CC=32）、`_build_proposal_detail`（CC=20）、`_build_evolution_status`（CC=11）、`_build_proposal_stats_json`，mock SQLite 查询与文件系统，重点覆盖 phases_json 解析和 proposal 状态机（预估复杂度：高, 预估 token：~6000 / 无历史参考）
- [ ] 6. **Dashboard HTTP handler 测试** — 覆盖 `_serve_dashboard.do_GET`（CC=16），验证路由分发（/api/status.json、/api/metrics.json、/api/pipeline-status 等），mock 内部构建函数（预估复杂度：中, 预估 token：~4000 / 无历史参考）

## 边界
### IN scope
- 新建 `tests/test_daemon.py`，包含上述 6 组模块的单元测试
- 使用 monkeypatch / unittest.mock 隔离 `_read_daemon_state`、SQLite 连接、文件系统、subprocess
- 验证 BAC：文件存在、至少 3 个 `def test_` 函数、`test__lock_path`/`test__daemon_state_path`/`test__read_daemon_state` 存在、pytest 退出码 0

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（含 2 个 lint 问题 F401/F541 不处理）
- 不修改已有测试文件 `test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`
- 不测试 `daemon_loop`（CC=51，已有 `test_daemon_scheduling.py` 覆盖调度逻辑）
- 不修改 `zsiga/metrics/db.py` 或 SQLite schema

### 依赖的外部条件
- `zsiga/daemon.py` 源码稳定，函数签名和返回结构不变
- 项目 Python 环境可运行 `python -m pytest tests/`
- 已有 `tests/conftest_zsiga.py` 可复用 fixture 模式

## 目标
### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥ 6 个 `def test_` 函数
2. 包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个指定测试
3. `python -m pytest tests/test_daemon.py` 退出码 0，全部测试通过
4. 覆盖 `_scan_proposal_queue`（CC=29）、`_build_pipeline_status`（CC=32）、`_build_proposal_detail`（CC=20）三个高 CC 函数
5. 所有测试通过 mock 隔离，不依赖运行时环境（无实际 daemon 进程、无实际 SQLite DB）

### 验收方式
- `ls tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 6
- `grep -E 'test__lock_path|test__daemon_state_path|test__read_daemon_state' tests/test_daemon.py` 确认 3 个指定测试
- `python -m pytest tests/test_daemon.py -v --tb=short` 退出码 0
- `ruff check tests/test_daemon.py` 无 lint 错误

## 约束
### 不能修改的文件
- `zsiga/daemon.py`
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`
- `tests/conftest_zsiga.py`
- `pyproject.toml`、`requirements.txt`

### 项目部署分支
- deploy

### 已知风险
- **历史循环风险**：此 proposal 已被生成 15+ 次，全部 skipped/pushbacked，零次成功执行。需确保本轮实现简洁、mock 策略正确，避免因测试间相互干扰导致 verify 失败
- **已有部分覆盖**：3 个现有测试文件已覆盖 `_write_daemon_state`、`daemon_loop` 调度、错误韧性。新测试需避免功能重复，聚焦未覆盖函数
- **高 CC 函数 mock 难度**：`_scan_proposal_queue`（CC=29）和 `_build_pipeline_status`（CC=32）内部分支多，需构造大量 fixture 数据覆盖关键路径
- **私有函数测试**：proposal 列出的函数绝大多数以 `_` 开头（private），需通过 `from zsiga.daemon import _lock_path` 等方式导入，可能随重构失效

### 预估 token 消耗
- prompt: ~4000
- completion: ~8000
- 数据来源: 无历史参考（此前执行均未成功完成）
