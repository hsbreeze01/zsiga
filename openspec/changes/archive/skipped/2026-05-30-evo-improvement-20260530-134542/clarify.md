# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行，21 函数，1 类）添加单元测试文件 `tests/test_daemon.py`，覆盖当前无直接测试的公开函数。模块已有 3 个侧面测试文件（`test_daemon_state.py` 覆盖 `_write_daemon_state`；`test_daemon_scheduling.py` 覆盖 `daemon_loop` 调度策略；`test_daemon_cycle_resilience.py` 覆盖 `daemon_loop` 错误韧性），但路径工具、锁管理、队列扫描、JSON 构建等核心函数仍无直接覆盖。

### 拆解后的子任务

- [ ] 1. **路径工具函数测试** — `_lock_path()`, `_daemon_state_path()`, `_read_daemon_state()`（预估复杂度：低, 预估 token：~1500 / 无历史参考）
  - 使用 `monkeypatch` 设置 `ZSIGA_HOME` / `tmp_path`，验证返回路径拼接正确性
  - `_read_daemon_state` 需覆盖文件不存在时返回默认 dict、文件存在且合法时返回内容、文件损坏时异常处理
  - 文件范围：`tests/test_daemon.py`（新建）

- [ ] 2. **PID 锁管理测试** — `acquire_lock()`, `release_lock(fd)`（预估复杂度：中, 预估 token：~2500 / 无历史参考）
  - `acquire_lock`：验证正常获取锁、锁文件已存在时的行为、异常时 cleanup
  - `release_lock`：验证 fd 关闭与锁文件删除
  - 需 mock `fcntl.flock` 或使用 `tmp_path` 隔离文件系统
  - 文件范围：`tests/test_daemon.py`

- [ ] 3. **提案队列扫描测试** — `_scan_proposal_queue(changes_dir)`（预估复杂度：高, 预估 token：~4000 / 无历史参考）
  - CC=29，90 行，是高复杂度函数，需覆盖多种目录结构场景
  - 空目录、含合法 proposal 子目录、含非 proposal 子目录、proposal 缺少必要文件、YAML 解析异常
  - 使用 `tmp_path` 构造目录树 mock
  - 文件范围：`tests/test_daemon.py`

- [ ] 4. **状态与指标 JSON 构建测试** — `_compute_uptime_seconds()`, `_build_status_json()`, `_build_metrics_json()`（预估复杂度：中, 预估 token：~3000 / 无历史参考）
  - `_compute_uptime_seconds`：传入不同时间戳验证计算正确性
  - `_build_status_json` / `_build_metrics_json`：mock `_read_daemon_state` 等内部依赖，验证输出 JSON 结构与关键字段
  - 文件范围：`tests/test_daemon.py`

- [ ] 5. **高复杂度 JSON 构建器测试** — `_build_pipeline_status()`, `_build_proposal_stats_json()`, `_build_proposal_detail()`, `_build_evolution_status()`（预估复杂度：高, 预估 token：~5000 / 无历史参考）
  - CC 分别为 32/11/20/11，需大量 mock 内部状态读取
  - 优先覆盖 happy path 和边界条件，不追求分支全覆盖
  - 使用 `unittest.mock.patch` 隔离 `_read_daemon_state`、文件系统读取等外部依赖
  - 文件范围：`tests/test_daemon.py`

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含对 `_lock_path`, `_daemon_state_path`, `_read_daemon_state`, `acquire_lock`, `release_lock`, `_scan_proposal_queue`, `_compute_uptime_seconds`, `_build_status_json`, `_build_metrics_json` 等函数的直接单元测试
- 补充 `_build_pipeline_status`, `_build_proposal_stats_json`, `_build_proposal_detail`, `_build_evolution_status` 的基础测试
- 每个测试函数可独立运行，不依赖运行时环境（daemon 进程、SQLite 数据库等）

### OUT of scope
- **不修改** `zsiga/daemon.py` 源码（包括不修复 L362 F401 未用 import 和 L965 F541 空 f-string）
- 不覆盖 `daemon_loop`（CC=51，已被 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 覆盖）
- 不覆盖 `_write_daemon_state`（已被 `test_daemon_state.py` 覆盖）
- 不覆盖 `_serve_dashboard.do_GET`（HTTP handler，属集成测试范畴）
- 不覆盖 `_build_current_json`、`_build_budget_analysis_json`、`_health_check`（可在后续 proposal 中处理）

### 依赖的外部条件
- `zsiga/daemon.py` 保持当前 API 签名不变
- 项目已有 `monkeypatch`/`tmp_path`/`unittest.mock` 使用先例（70+ 测试文件可参考）
- `pytest` + `ruff` 工具链可用

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且通过 `ruff check` 无错误
2. 包含至少 10 个 `def test_` 函数，覆盖上述 5 个功能模块
3. `python -m pytest tests/test_daemon.py` 退出码 0，所有测试通过
4. `python -m pytest tests/test_daemon.py tests/test_daemon_state.py tests/test_daemon_scheduling.py tests/test_daemon_cycle_resilience.py` 全部通过（不破坏已有测试）
5. 至少覆盖 `_lock_path`, `_daemon_state_path`, `_read_daemon_state`, `acquire_lock`, `release_lock`, `_scan_proposal_queue` 这 6 个当前零覆盖函数

### 验收方式
- `test -f tests/test_daemon.py` 验证文件存在
- `grep -c 'def test_' tests/test_daemon.py` 验证测试数量 ≥ 10
- `python -m pytest tests/test_daemon.py -v --tb=short` 验证全部通过
- `ruff check tests/test_daemon.py` 验证无 lint 错误
- 运行全部 daemon 相关测试确认无回归

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析，不修改源码
- `tests/test_daemon_state.py` — 已有测试，不修改
- `tests/test_daemon_scheduling.py` — 已有测试，不修改
- `tests/test_daemon_cycle_resilience.py` — 已有测试，不修改

### 项目部署分支
- `main`

### 已知风险
- **proposal 循环风险**：此 proposal 已被自演进引擎生成 27+ 次且从未成功执行，需确保本轮 BAC 足够严格（≥10 个测试函数覆盖 ≥6 个零覆盖函数），避免与历史版本同质化被再次拦截
- **高 CC 函数 mock 成本**：`_scan_proposal_queue`(CC=29) 和 `_build_pipeline_status`(CC=32) 分支众多，完全覆盖 mock 成本极高，应优先覆盖核心路径而非追求 100% 分支覆盖
- **内部函数签名不稳定**：部分函数依赖模块级常量（`ZSIGA_HOME`）和全局状态，需通过 `monkeypatch` 隔离
- **与已有测试重叠**：`test_daemon_state.py` 已覆盖 `_write_daemon_state`，新文件不应重复覆盖同一函数

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（前 27 次 proposal 均未到达执行阶段）
