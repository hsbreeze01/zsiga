# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行，21 函数，1 类）创建 `tests/test_daemon.py` 单元测试文件。模块目前虽有 3 个间接测试文件（`test_daemon_state.py` 242 行、`test_daemon_scheduling.py` 421 行、`test_daemon_cycle_resilience.py` 213 行），但 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`(CC=29)、`_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20) 等核心函数仍无直接覆盖。需新建独立测试文件，用 mock 隔离外部依赖，优先覆盖高复杂度函数。

### 拆解后的子任务

- [ ] 1. **路径与状态工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`，验证路径拼接逻辑和状态文件读取/缺省值。满足 BAC-02 要求的 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state`。(预估复杂度：低, 预估 token：~2000)
- [ ] 2. **文件锁管理测试** — 覆盖 `acquire_lock()` 和 `release_lock(fd)`，验证锁文件创建、flock 行为和 fd 关闭。使用 tmp_path 隔离文件系统。(预估复杂度：中, 预估 token：~2500)
- [ ] 3. **提案队列扫描测试** — 覆盖 `_scan_proposal_queue(changes_dir)`（CC=29，90 行），测试空目录/有效提案/损坏 proposal/混合状态等分支路径。用 monkeypatch 隔离 changes_dir。(预估复杂度：高, 预估 token：~3500)
- [ ] 4. **状态/指标 JSON 构建器测试** — 覆盖 `_compute_uptime_seconds()`、`_build_status_json()`、`_build_metrics_json()`、`_build_current_json()` 等纯计算/序列化函数。验证输出结构和关键字段。(预估复杂度：低, 预估 token：~2000)
- [ ] 5. **Dashboard 详情构建器测试** — 覆盖 `_build_pipeline_status()`（CC=32）、`_build_proposal_detail()`（CC=20）、`_build_evolution_status()`（CC=11）三个高复杂度函数。mock orchestrator 和文件系统，测试各分支返回值结构。(预估复杂度：高, 预估 token：~3500)
- [ ] 6. **Dashboard HTTP handler 测试** — 覆盖 `_serve_dashboard` 内部 `do_GET` 方法（CC=16），模拟 HTTP 请求验证路由和响应。确保满足 BAC-03（至少 3 个 `def test_` 函数）和 BAC-04（pytest 退出码 0）。(预估复杂度：中, 预估 token：~2500)

## 边界

### IN scope
- 创建 `tests/test_daemon.py`，包含上述函数的单元测试
- 使用 mock（`unittest.mock.patch`/`monkeypatch`）隔离文件 I/O、subprocess、LLM 调用等外部依赖
- 优先覆盖 CC>10 的高复杂度函数（`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`）
- 满足全部 4 条 BAC

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复 2 个 lint 问题：L362 F401 和 L965 F541）
- 不修改已有的 3 个 daemon 测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）
- 不对 `daemon_loop`（CC=51，309 行）做完整覆盖——其调度逻辑已被 `test_daemon_scheduling.py` 覆盖
- 不修改项目配置文件（`pyproject.toml`、`requirements.txt`）

### 依赖的外部条件
- `zsiga/daemon.py` 模块可正常 import（无缺失依赖）
- pytest 和 `unittest.mock` 可用（项目已依赖）
- 现有测试套件不因新增文件而回归（`python -m pytest tests/` 通过）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥ 3 个 `def test_` 函数
2. 文件中包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个测试函数（满足 BAC-02）
3. `python -m pytest tests/test_daemon.py` 退出码为 0（满足 BAC-04）
4. 新增测试不破坏现有测试套件（`python -m pytest tests/` 退出码 0）
5. 优先覆盖 `_scan_proposal_queue`(CC=29)、`_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20) 三大高复杂度函数

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 3
- `grep -q 'test__lock_path\|test__daemon_state_path\|test__read_daemon_state' tests/test_daemon.py` 确认关键测试存在
- `python -m pytest tests/test_daemon.py -v` 退出码 0
- `python -m pytest tests/ --tb=short` 退出码 0（回归检查）

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（仅读取分析，不修改）
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
- deploy (根据项目配置，target project=zsiga 自身)

### 已知风险
- **已有测试重叠**：`test_daemon_state.py` 已覆盖 `_write_daemon_state`，`test_daemon_scheduling.py` 已覆盖 `daemon_loop` 调度逻辑。新测试应避免重复覆盖已有函数，专注于未覆盖的函数。
- **高复杂度函数 mock 成本**：`_build_pipeline_status`(CC=32) 和 `_build_proposal_detail`(CC=20) 依赖 orchestrator 状态和文件系统，mock 链路较长。
- **zombie loop 风险**：同题 proposal 在 archive 中有 20+ 个被跳过/拒绝的历史版本，需确保 BAC 足够收紧以产生实际价值。
- **`_serve_dashboard` 内部类**：`do_GET` 是 `_serve_dashboard` 内的 `handler_class` 方法，需通过间接方式测试（如构造 handler 实例或 mock socketserver）。

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: 无历史参考（同类 daemon 测试 proposal 均未成功执行过，按新建 ~200 行测试文件估算）
