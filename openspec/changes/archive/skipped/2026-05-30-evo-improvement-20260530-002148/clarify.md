# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行、21 函数、1 类）新建 `tests/test_daemon.py`，补齐当前零覆盖的函数单元测试。已有 3 个 daemon 相关测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）覆盖了 `_write_daemon_state`、`daemon_loop` 调度策略、错误恢复等场景，**新文件不应重复这些覆盖**。

### 拆解后的子任务

- [ ] 1. **路径与状态工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`、`_compute_uptime_seconds()` (预估复杂度：低, 预估 token：~1500)
  - 范围：4 个低复杂度纯函数/简单函数
  - 测试类：`TestPathHelpers`、`TestReadDaemonState`、`TestComputeUptime`
  - mock 策略：`monkeypatch` 替换路径前缀、`tmp_path` 构造状态文件
  - 预期 ≥5 个 `def test_` 函数

- [ ] 2. **文件锁生命周期测试** — 覆盖 `acquire_lock()`、`release_lock(fd)` (预估复杂度：中, 预估 token：~1200)
  - 范围：2 个函数，涉及 `os.open`/`fcntl.flock`/`os.close` 系统调用
  - 测试类：`TestLockLifecycle`
  - mock 策略：`unittest.mock.patch` mock `os.open`、`fcntl.flock`、`os.close`；测试获取成功、释放成功、获取失败（已锁定）路径
  - 预期 ≥4 个 `def test_` 函数

- [ ] 3. **队列扫描逻辑测试** — 覆盖 `_scan_proposal_queue(changes_dir)` (CC=29) (预估复杂度：高, 预估 token：~2500)
  - 范围：1 个高复杂度函数（90 行，CC=29），含目录遍历、状态过滤、优先级排序、时间排序
  - 测试类：`TestScanProposalQueue`
  - mock 策略：`tmp_path` 构造 `changes_dir` 目录树（含不同状态的子目录：`proposal.md` 存在/缺失、`steward-review` 存在/缺失、`skip` 标记存在等）
  - 预期 ≥6 个 `def test_` 函数（空目录、单 proposal、多 proposal 排序、已处理跳过、损坏目录处理等）

- [ ] 4. **JSON 构建函数测试** — 覆盖 `_build_status_json()`、`_build_metrics_json()`、`_build_pipeline_status()`、`_build_proposal_detail()`、`_build_evolution_status()` (预估复杂度：中, 预估 token：~2000)
  - 范围：5 个 JSON 序列化函数，输入为 daemon state / proposal 数据，输出为 dict
  - 测试类：`TestBuildStatusJson`、`TestBuildMetricsJson`、`TestBuildPipelineStatus`、`TestBuildProposalDetail`、`TestBuildEvolutionStatus`
  - mock 策略：`monkeypatch` 或 `patch` mock `_read_daemon_state`、`_compute_uptime_seconds`；构造固定输入数据验证输出字段
  - 预期 ≥7 个 `def test_` 函数

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含 ≥4 个测试类、≥22 个 `def test_` 函数
- 覆盖 proposal 中列出的 10 个函数 + `_build_pipeline_status` + `_build_proposal_detail` + `_build_evolution_status` 共 13 个函数
- 测试文件必须包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state`（BAC-02 要求）
- 所有测试通过 `python -m pytest tests/test_daemon.py` 且退出码 0
- 使用项目已有测试模式：`TestXxx` 类分组、`monkeypatch`/`patch` mock、`tmp_path` 文件 fixture

### OUT of scope
- **不修改** `zsiga/daemon.py` 源码（只读取分析）
- **不覆盖** `_write_daemon_state`（已有 `test_daemon_state.py` 完整覆盖）
- **不覆盖** `daemon_loop` 主循环调度逻辑（已有 `test_daemon_scheduling.py` 覆盖调度策略、`test_daemon_cycle_resilience.py` 覆盖错误恢复）
- **不覆盖** `_serve_dashboard` / `do_GET` HTTP 服务（需要 HTTP server fixture，复杂度过高且风险收益比低）
- **不修复** `daemon.py` 中已知的 2 个 lint 问题（L362 F401、L965 F541）

### 依赖的外部条件
- `fcntl` 模块可用（Linux 环境，锁测试需要）
- `zsiga.daemon` 模块可正常 import
- 已有 conftest fixture（`tests/conftest_zsiga.py`）可复用

## 目标

### 成功标准
1. `tests/test_daemon.py` 存在且包含 ≥4 个 `class Test*` 类
2. 包含 ≥22 个 `def test_` 函数，覆盖 13 个目标函数
3. `python -m pytest tests/test_daemon.py -v` 全部通过，退出码 0
4. `ruff check tests/test_daemon.py` 无错误
5. 与已有 3 个 daemon 测试文件无重复覆盖（`_write_daemon_state`、`daemon_loop` 调度不在新文件中测试）

### 验收方式
- `[BAC-01]` `ls tests/test_daemon.py` 退出码 0
- `[BAC-02]` `grep -c 'def test__lock_path\|def test__daemon_state_path\|def test__read_daemon_state' tests/test_daemon.py` ≥ 3
- `[BAC-03]` `grep -c 'def test_' tests/test_daemon.py` ≥ 22
- `[BAC-04]` `python -m pytest tests/test_daemon.py` 退出码 0
- 额外检查：`ruff check tests/test_daemon.py` 退出码 0
- 额外检查：`grep -c 'class Test' tests/test_daemon.py` ≥ 4

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（只读）
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`
- `tests/conftest_zsiga.py`
- `zsiga.yaml`

### 项目部署分支
deploy

### 已知风险
- `_scan_proposal_queue` CC=29，内部逻辑复杂（目录遍历 + 多条件过滤 + 排序），测试用例设计需要覆盖足够多的分支路径
- `acquire_lock` / `release_lock` 依赖 `fcntl`，在 CI 环境中可能需要 mock；若直接使用 `tmp_path` 创建锁文件需确保测试间无竞争
- `_build_pipeline_status` (CC=32) 和 `_build_proposal_detail` (CC=20) 输入结构复杂，需要构造较大 fixture 数据
- proposal 历史 10+ 次 PUSHBACK/SKIP，需确保本次 BAC 具体且可自动验证

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: historical（参考 `test_daemon_state.py` 10 测试 ~200 行、`test_daemon_scheduling.py` 9 测试 ~250 行的规模比例）
