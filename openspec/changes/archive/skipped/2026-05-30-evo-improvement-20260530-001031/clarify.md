# clarify.md — add-tests-daemon

## 需求拆解
### 原始需求
为无测试模块 `zsiga/daemon.py`（1110 行, 21 函数, 1 类）新建 `tests/test_daemon.py`，覆盖公开/可测函数的单元测试。不修改源码。

### 拆解后的子任务

- [ ] 1. **路径与状态工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`、`_compute_uptime_seconds(started_at)` (预估复杂度：低, 预估 token：~3000 / 无历史参考)
  - 文件范围：`tests/test_daemon.py` 新建，`zsiga/daemon.py` L34-L226 只读
  - 测试类：`TestPathHelpers`（2-3 个 case）、`TestReadDaemonState`（3-4 个 case：正常/文件不存在/空内容/损坏 JSON）、`TestComputeUptimeSeconds`（3-4 个 case：正常/None/空字符串/非法格式）
  - Mock 策略：`monkeypatch` 设置 `data/` 目录；`tmp_path` 隔离文件 I/O

- [ ] 2. **锁管理函数测试** — 覆盖 `acquire_lock()`、`release_lock(fd)` (预估复杂度：中, 预估 token：~2500 / 无历史参考)
  - 文件范围：`tests/test_daemon.py`，`zsiga/daemon.py` L94-L119 只读
  - 测试类：`TestLockLifecycle`（4-5 个 case：获取锁成功/锁文件已存在(模拟 EEXIST)/释放锁/释放后文件删除/异常路径 fd 无效）
  - Mock 策略：`tmp_path` 创建临时锁目录；`monkeypatch.setattr` 替换 `_lock_path` 返回临时路径；需处理 `os.open` / `os.close` / `os.remove` 的边界情况

- [ ] 3. **队列扫描函数测试** — 覆盖 `_scan_proposal_queue(changes_dir)`（CC=29, L122-L211） (预估复杂度：高, 预估 token：~5000 / 无历史参考)
  - 文件范围：`tests/test_daemon.py`，`zsiga/daemon.py` L122-L211 只读
  - 测试类：`TestScanProposalQueue`（6-8 个 case：空目录/正常提案排序/paused 状态跳过/consecutive_fails 标记/缺少 proposal.md 的目录/多个项目混合/.phase_state 解析）
  - Mock 策略：`tmp_path` 构造目录树（每个 case 一个 fixture），模拟 `openspec/changes/<name>/proposal.md` + `.phase_state` 文件结构
  - 注意：CC=29，需覆盖分支：paused 检测、lifecycle 判断、consecutive_fails 阈值、project 提取

- [ ] 4. **JSON 构建函数测试** — 覆盖 `_build_status_json()`、`_build_metrics_json()` (预估复杂度：低, 预估 token：~2500 / 无历史参考)
  - 文件范围：`tests/test_daemon.py`，`zsiga/daemon.py` L229-L262 只读
  - 测试类：`TestBuildStatusJson`（2-3 个 case：正常结构/关键字段存在）、`TestBuildMetricsJson`（2-3 个 case：正常结构/DB 不存在时降级）
  - Mock 策略：`monkeypatch` 替换 `_read_daemon_state` 返回 fixture 数据；`patch` 隔离 `zsiga.metrics.db` 的 DB 依赖

## 边界
### IN scope
- 新建 `tests/test_daemon.py`，覆盖以下 10 个函数：`_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`_compute_uptime_seconds`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_build_status_json`、`_build_metrics_json`
- 测试 `DaemonState` dataclass 默认值（`paused=False, shutdown=False`）
- 使用 `pytest` + `monkeypatch` + `tmp_path` + `unittest.mock.patch` 隔离外部依赖

### OUT of scope
- **不修改** `zsiga/daemon.py` 源码（包括修复 L362 F401 和 L965 F541 lint 问题）
- 高 CC 函数暂不覆盖：`daemon_loop`（CC=51）、`_build_pipeline_status`（CC=32）、`_build_proposal_detail`（CC=20）、`_build_evolution_status`（CC=11）、`_serve_dashboard.do_GET`（CC=16）
- 不与已有测试文件重叠：`test_daemon_cycle_resilience.py`（错误隔离）、`test_daemon_scheduling.py`（调度策略）、`test_daemon_state.py`（`_write_daemon_state`）
- 不测试 HTTP handler `_serve_dashboard` 类

### 依赖的外部条件
- `zsiga/daemon.py` 模块可正常 import（无语法错误）
- 已有 `tests/test_daemon_state.py` 等文件作为测试模式参考
- 项目已有 `conftest_zsiga.py` 提供 pytest fixture 基础设施

## 目标
### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥4 个 `class Test*` 测试类
2. 覆盖 10 个目标函数中至少 8 个（每个函数至少 1 个正向 + 1 个边界 case）
3. `_scan_proposal_queue`（CC=29）至少 6 个测试 case，覆盖空目录、排序、paused、consecutive_fails 分支
4. `python -m pytest tests/test_daemon.py -v` 退出码 0，全部 case PASS
5. `ruff check tests/test_daemon.py` 无错误

### 验收方式
- `ls tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 15
- `python -m pytest tests/test_daemon.py -v --tb=short` 全绿
- `ruff check tests/test_daemon.py` 零错误

## 约束
### 不能修改的文件
- `zsiga/daemon.py`（仅读取分析，不修改）
- `tests/test_daemon_cycle_resilience.py`（已有覆盖，不重叠）
- `tests/test_daemon_scheduling.py`（已有覆盖，不重叠）
- `tests/test_daemon_state.py`（已有覆盖，不重叠）

### 项目部署分支
- deploy（需在 change 完成后由 DELIVER 阶段合入）

### 已知风险
- `_scan_proposal_queue` CC=29，内部分支密集，测试需仔细构造目录树 fixture 以覆盖主路径
- `_build_metrics_json` 和 `_build_status_json` 可能依赖 `zsiga.metrics.db` 的 SQLite 连接，需 mock 隔离
- `acquire_lock` 使用 `os.open` + `O_CREAT | O_EXCL`，在并发测试中需确保 `tmp_path` 隔离
- 自演进引擎曾 10+ 次生成同名 proposal 被 skip/pushback，需确保本次测试质量显著高于历史尝试

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（基于 4 个子任务的代码量估算：10 个目标函数 × 平均 40 行测试 = 400 行测试代码）
