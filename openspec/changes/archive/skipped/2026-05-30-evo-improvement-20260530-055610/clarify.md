# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行，21 函数，1 类）新建单元测试文件 `tests/test_daemon.py`。现有 4 个分散测试文件（`test_daemon_state.py`、`test_daemon_cycle_resilience.py`、`test_daemon_scheduling.py`、`test_dashboard_api.py`）已覆盖部分函数（`_write_daemon_state`、`daemon_loop` 错误隔离/调度），但以下函数**无任何测试覆盖**，是本 proposal 的真正目标。

### 拆解后的子任务

- [ ] 1. **路径与状态读取函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()` 三个纯路径/IO 函数（预估复杂度：低，预估 token：~1500 / 无历史参考）
  - 文件范围：`tests/test_daemon.py`（新建），`zsiga/daemon.py`（仅读取）
  - 技术：monkeypatch `ZSIGA_HOME` 环境变量，用 `tmp_path` 隔离文件 IO
- [ ] 2. **文件锁函数测试** — 覆盖 `acquire_lock()` 和 `release_lock(fd)`（预估复杂度：中，预估 token：~2000 / 无历史参考）
  - 文件范围：`tests/test_daemon.py`，`zsiga/daemon.py`（仅读取）
  - 技术：`tmp_path` 创建锁文件，验证 fcntl 行为，测试重复加锁冲突
- [ ] 3. **队列扫描与状态构建函数测试** — 覆盖 `_compute_uptime_seconds()`、`_build_status_json()`、`_build_metrics_json()`（预估复杂度：低，预估 token：~1500 / 无历史参考）
  - 文件范围：`tests/test_daemon.py`，`zsiga/daemon.py`（仅读取）
  - 技术：monkeypatch 全局状态变量，验证 JSON 输出结构

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，覆盖以下无测试函数：`_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`
- 使用 mock/monkeypatch 隔离外部依赖（文件 IO、fcntl）
- 满足 BAC-01 到 BAC-04（文件存在、3 个指定函数名、≥3 个 test_、pytest 退出码 0）

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复 2 个 lint 问题）
- 不覆盖已有测试文件的函数（`_write_daemon_state` 已由 `test_daemon_state.py` 覆盖；`daemon_loop` 已由 `test_daemon_cycle_resilience.py` 和 `test_daemon_scheduling.py` 覆盖）
- 不覆盖高 CC 函数（`_scan_proposal_queue` CC=29、`_build_pipeline_status` CC=32、`daemon_loop` CC=51）— 这些需要大量 mock 链，超出 BAC 最小要求
- 不与现有 4 个测试文件合并或重构

### 依赖的外部条件
- `pytest` 框架已就绪（项目有 70+ 测试文件）
- `monkeypatch` fixture 可用（项目广泛使用此模式）
- `fcntl` 模块可用（Linux 环境，`acquire_lock` 测试依赖）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个函数
2. 文件中包含至少 3 个 `def test_` 函数
3. `python -m pytest tests/test_daemon.py` 退出码为 0，全部测试通过
4. 新测试不与现有测试文件产生冲突（`pytest tests/` 整体仍通过）

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 3
- `grep -E 'def test__(lock_path|daemon_state_path|read_daemon_state)' tests/test_daemon.py` 确认 3 个指定函数
- `python -m pytest tests/test_daemon.py -v --tb=short` 退出码 0

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析，不修改
- 现有测试文件（`test_daemon_state.py`、`test_daemon_cycle_resilience.py`、`test_daemon_scheduling.py`、`test_dashboard_api.py`）— 不合并/不重构

### 项目部署分支
- `zsiga` (project=zsiga)

### 已知风险
- **15+ 轮循环空转**：同名 proposal 已反复生成 15+ 次全部被 skip/pushback，需确保本轮 BAC 最小化、scope 收敛，避免再次空转
- **现有测试冲突**：新测试中 monkeypatch 的全局状态可能与现有测试 fixture 冲突，需使用 `tmp_path` 和局部 mock 隔离
- **fcntl 平台限制**：`acquire_lock` 使用 `fcntl.flock`，仅 Linux/Mac 可用，Windows CI 会跳过

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考（同名 proposal 从未到达执行阶段）
