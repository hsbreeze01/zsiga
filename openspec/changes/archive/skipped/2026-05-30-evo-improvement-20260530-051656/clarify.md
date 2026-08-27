# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行，21 函数，1 类 `DaemonState`）创建单元测试文件 `tests/test_daemon.py`。该模块已有 3 个间接/部分测试文件（`test_daemon_state.py` 覆盖 `_write_daemon_state`，`test_daemon_cycle_resilience.py` 覆盖 `daemon_loop` 错误隔离，`test_daemon_scheduling.py` 覆盖调度策略），但约 15 个函数缺乏直接单元测试，其中 4 个高圈复杂度函数（CC≥11）风险最高。

### 拆解后的子任务

- [ ] 1. **路径与状态读取工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()` 三个低 CC 辅助函数。验证路径拼接逻辑和空文件/缺失文件的优雅降级。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 2. **文件锁生命周期测试** — 覆盖 `acquire_lock()` 和 `release_lock(fd)`。需要 mock `fcntl.flock`（POSIX-only）和文件描述符操作，验证锁定/释放路径和异常处理。（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 3. **提案队列扫描测试** — 覆盖 `_scan_proposal_queue(changes_dir)`（CC=29, 90 行）。构造多种 changes_dir 目录结构（空目录、有效/无效 proposal、混合状态），验证分类逻辑（pending/active/completed/failed）和排序。（预估复杂度：高, 预估 token：~8000 / 无历史参考）
- [ ] 4. **状态与指标构建器测试** — 覆盖 `_compute_uptime_seconds(started_at)`、`_build_status_json()`、`_build_metrics_json()`。验证时间计算、JSON 序列化输出格式。需要 monkeypatch `_read_daemon_state` 和 `os.path.exists`。（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 5. **Dashboard 数据聚合测试** — 覆盖 `_build_pipeline_status()`（CC=32）、`_build_proposal_detail()`（CC=20）、`_build_evolution_status()`（CC=11）。这三个高复杂度函数依赖大量外部状态，需 mock `_read_daemon_state`、`os.listdir`、文件读取、subprocess 等。重点验证分支覆盖和边界条件。（预估复杂度：高, 预估 token：~10000 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含上述 5 组功能的单元测试
- 覆盖 BAC 要求的 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state`
- 至少 15 个 `def test_` 函数（覆盖低 CC 辅助函数 + 高 CC 核心逻辑）
- 使用 `monkeypatch`、`tmp_path`、`unittest.mock` 隔离文件 I/O、`fcntl`、subprocess

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括 2 个 lint 问题：L362 F401、L965 F541）
- 不覆盖已有间接测试的 `daemon_loop`、`_write_daemon_state`、`_serve_dashboard.do_GET`
- 不覆盖 `DaemonState` dataclass（无方法，构造即验证）
- 不引入新的 conftest fixture 文件

### 依赖的外部条件
- `fcntl` 模块可用（POSIX 环境，测试环境需为 Linux/macOS）
- `zsiga/daemon.py` 的公开接口在测试编写期间不发生 breaking change
- 现有 3 个 daemon 测试文件（`test_daemon_state.py`、`test_daemon_cycle_resilience.py`、`test_daemon_scheduling.py`）保持不变，新测试不与之冲突

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含至少 15 个 `def test_` 函数
2. BAC 要求的 3 个测试函数（`test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state`）存在
3. `python -m pytest tests/test_daemon.py` 退出码 0，无 skip/error
4. 覆盖至少 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json` 共 9 个函数的直接测试
5. 高 CC 函数（`_scan_proposal_queue` CC=29）至少有 5 个测试用例覆盖不同分支

### 验收方式
- `[ -f tests/test_daemon.py ]` 文件存在性检查
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 15
- `grep -q 'def test__lock_path\|def test__daemon_state_path\|def test__read_daemon_state' tests/test_daemon.py` BAC-02 符合性
- `python -m pytest tests/test_daemon.py -v --tb=short` 退出码 0
- `python -m ruff check tests/test_daemon.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析，不做任何修改
- `tests/test_daemon_state.py` — 已有覆盖，不重复
- `tests/test_daemon_cycle_resilience.py` — 已有覆盖，不重复
- `tests/test_daemon_scheduling.py` — 已有覆盖，不重复
- `tests/conftest_zsiga.py` — 不添加新 fixture
- `zsiga.yaml` — 不修改项目配置

### 项目部署分支
deploy（以 `zsiga.yaml` 中 `targets.zsiga.deploy_branch` 为准）

### 已知风险
- **fcntl 平台依赖**：`acquire_lock`/`release_lock` 使用 `fcntl.flock`，在非 POSIX 环境（Windows CI）会 `ImportError`，需 `@pytest.mark.skipif` 守护或 mock 隔离
- **高 CC 函数 mock 复杂度**：`_build_pipeline_status`（CC=32）依赖大量外部状态（daemon_state、changes_dir 目录结构、sqlite3 数据库），mock 链可能冗长且脆弱
- **16+ 次迭代未交付**：此 proposal 已被 SKIP/PUSHBACK 16+ 次，历史成功率为 0%，需严格控制 scope 避免 over-engineering
- **daemon.py 可能有隐式全局状态**：模块级 `logging.getLogger`、`ZSIGA_HOME` 环境变量依赖等，需 monkeypatch 隔离

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考（同类 proposal 从未成功交付，无 token 消耗基线）
