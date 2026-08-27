# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行，21 函数，1 类）创建单元测试文件 `tests/test_daemon.py`，重点覆盖 6 个高复杂度函数（CC>10），使用 mock 隔离外部依赖。

### 拆解后的子任务

- [ ] 1. **测试基础设施搭建** — 创建 `tests/test_daemon.py`，建立 fixture 体系（`tmp_path` 路径隔离、`monkeypatch` 替换 `_daemon_state_path`/`_lock_path`、`DaemonState` mock），确保 import 链正确。（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. **低复杂度辅助函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`、`_write_daemon_state()`、`_compute_uptime_seconds()` 等纯函数，验证路径生成、JSON 读写、时间计算。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 3. **锁管理函数测试** — 覆盖 `acquire_lock()`、`release_lock(fd)`，mock 文件 I/O，验证锁文件创建/释放/异常路径（已锁定、权限错误）。（预估复杂度：中, 预估 token：~3000 / 无历史参考）
- [ ] 4. **高复杂度函数测试：`_scan_proposal_queue`**（CC=29）— 覆盖目录扫描、proposal 排序、过滤逻辑，mock `os.listdir`/`os.path.isdir` 构造多种目录布局（空目录、无效名称、混合状态）。（预估复杂度：高, 预估 token：~5000 / 无历史参考）
- [ ] 5. **高复杂度函数测试：`_build_pipeline_status` + `_build_proposal_detail`**（CC=32/20）— 覆盖状态 JSON 构建，mock 数据库查询和文件系统读取，验证多 proposal 状态聚合逻辑。（预估复杂度：高, 预估 token：~5000 / 无历史参考）
- [ ] 6. **状态/指标 API 函数测试** — 覆盖 `_build_status_json()`、`_build_metrics_json()`、`_build_evolution_status()`（CC=11），验证 JSON 输出结构和字段完整性。（预估复杂度：中, 预估 token：~3000 / 无历史参考）
- [ ] 7. **pytest 执行验证** — 运行 `python -m pytest tests/test_daemon.py -x` 确认退出码 0，同时运行 `ruff check tests/test_daemon.py` 确认无 lint 错误。（预估复杂度：低, 预估 token：~1000 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，覆盖 `zsiga/daemon.py` 中所有可独立测试的函数
- 优先覆盖 6 个高 CC 函数：`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`、`_build_evolution_status`、`_serve_dashboard.do_GET`、`daemon_loop`
- 使用 mock 隔离：LLM 调用、文件 I/O、subprocess、数据库
- 遵循已有 daemon 测试的模式（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括修复其 2 个 lint 问题）
- 不修改已有的 `tests/test_daemon_state.py`、`tests/test_daemon_scheduling.py`、`tests/test_daemon_cycle_resilience.py`
- 不覆盖 `daemon_loop`（CC=51，已在 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 中有 634 行覆盖）
- 不覆盖 `_serve_dashboard.do_GET`（HTTP handler 需要完整服务器 mock，投入产出比低）

### 依赖的外部条件
- `zsiga/daemon.py` 当前接口不变（函数签名、import 结构稳定）
- pytest 和 monkeypatch fixture 可用（项目已使用）
- 已有 daemon 测试中的 mock 模式可参考（`_AutoShutdownState`、路径隔离）

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥10 个 `def test_` 函数
2. 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`_write_daemon_state`、`acquire_lock`、`release_lock`、`_scan_proposal_queue`、`_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`、`_build_pipeline_status`、`_build_proposal_detail`、`_build_evolution_status` 中的至少 10 个函数
3. `python -m pytest tests/test_daemon.py -x` 退出码 0
4. `python -m ruff check tests/test_daemon.py` 无错误

### 验收方式
- `test -f tests/test_daemon.py` 确认文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥10
- `python -m pytest tests/test_daemon.py -x --tb=short` 退出码 0
- `python -m ruff check tests/test_daemon.py` 无输出

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（仅读取分析）
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`
- `zsiga/config.py` 及所有 pipeline/agent 源码

### 项目部署分支
- `zsiga` target 的 `deploy_branch`（需从 `zsiga.yaml` 中确认，默认为当前工作分支）

### 已知风险
- **历史失败**：此 proposal 已被 pushback/skip 10+ 次，需避免之前的问题（BAC 过弱、测试空洞、与已有测试重叠）
- **与已有测试重叠**：`test_daemon_state.py` 已覆盖 `_write_daemon_state`，`test_daemon_scheduling.py` 已覆盖 `daemon_loop` 调度逻辑。新测试应专注于**尚未覆盖的函数**，避免重复
- **`_scan_proposal_queue` 依赖文件系统**：需构造 `tmp_path` 目录结构 mock，复杂度高
- **`_build_pipeline_status` 可能依赖数据库**：需确认是否直接查询 SQLite，若是则需 mock `zsiga.metrics.db`

### 预估 token 消耗
- prompt: ~15000
- completion: ~8000
- 数据来源: 无历史参考（基于模块复杂度和函数数量估算）
