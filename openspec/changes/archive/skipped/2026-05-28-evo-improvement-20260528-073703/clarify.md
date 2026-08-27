# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1085 行，21 函数，1 类，6 个高 CC 函数）新建 `tests/test_daemon.py`，提供单元测试覆盖。已有 3 个侧面测试文件（`test_daemon_state.py` 242L/10 tests、`test_daemon_scheduling.py` 421L/12 tests、`test_daemon_cycle_resilience.py` 213L/7 tests），但缺少针对高复杂度函数（`_scan_proposal_queue` CC=29、`_build_pipeline_status` CC=32、`_build_proposal_detail` CC=20）的直接测试。

### 拆解后的子任务

- [ ] 1. **基础工具函数测试** — 覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`，满足 BAC-02 最低要求（预估复杂度：低，预估 token：~2000 / 无历史参考）
- [ ] 2. **提案队列扫描测试 `_scan_proposal_queue`** — 覆盖空队列、正常队列、损坏 proposal 文件、缺少 proposal.md、子目录嵌套等分支（CC=29, 90L，需 mock `config.load_config()`、文件系统）（预估复杂度：高，预估 token：~4000 / 无历史参考）
- [ ] 3. **Pipeline 状态构建测试 `_build_pipeline_status`** — 覆盖正常流程、空 changes、多 proposal 状态聚合、异常路径（CC=32, 103L，需 mock SQLite/metrics.db、文件系统、daemon_state）（预估复杂度：高，预估 token：~4000 / 无历史参考）
- [ ] 4. **Proposal 详情构建测试 `_build_proposal_detail`** — 覆盖完整 proposal、缺失字段、部分阶段完成等场景（CC=20, 76L）（预估复杂度：中，预估 token：~3000 / 无历史参考）
- [ ] 5. **辅助函数测试** — 覆盖 `_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`（预估复杂度：低，预估 token：~2000 / 无历史参考）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`
- 测试 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`（BAC-02 强制要求）
- 测试 `_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`（高 CC 优先覆盖）
- 测试 `_compute_uptime_seconds`、`_build_status_json`、`_build_metrics_json`
- 使用 monkeypatch / tmp_path / unittest.mock 隔离外部依赖

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括 lint 问题 L362 F401、L948 F541）
- 不修改已有的 3 个 daemon 测试文件
- 不测试 `daemon_loop()`（CC=43, 284L，需完整状态机 mock，超出单次 proposal 合理范围）
- 不测试 `_serve_dashboard.do_GET()`（HTTP handler，需 HTTP 层 mock）
- 不测试 `acquire_lock()` / `release_lock()`（跨进程文件锁，需集成测试环境）
- 不测试 `_build_evolution_status()`（CC=11，可后续迭代）

### 依赖的外部条件
- `zsiga/daemon.py` 可被正常 import（依赖 `zsiga.config`、`zsiga.metrics.db` 等）
- pytest 基础设施可用（`conftest_zsiga.py` 提供 fixture 支持）
- 已有测试文件中的 mock 模式可参考（`test_daemon_state.py` 使用 monkeypatch 替换 `_daemon_state_path`）

## 目标

### 成功标准
1. `tests/test_daemon.py` 存在且包含至少 3 个 `def test_` 函数
2. 包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个函数名（BAC-02）
3. `pytest tests/test_daemon.py` 退出码 0
4. 高 CC 函数（`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`）至少各有一个测试用例
5. 所有测试使用 mock 隔离，不依赖运行时环境（无真实 LLM 调用、无真实文件 I/O 到项目目录）

### 验收方式
- `test -f tests/test_daemon.py` 验证文件存在
- `grep -c 'def test_' tests/test_daemon.py` 计数 ≥ 3
- `grep -E 'def test__lock_path|def test__daemon_state_path|def test__read_daemon_state' tests/test_daemon.py` 验证 BAC-02
- `python -m pytest tests/test_daemon.py -v` 退出码 0，所有测试 PASS
- `python -m ruff check tests/test_daemon.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（源码不可变）
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`
- `tests/conftest_zsiga.py`

### 项目部署分支
- `zsiga` target 的部署分支（见 `zsiga.yaml` targets 配置）

### 已知风险
- **高 CC 函数 mock 复杂度高**：`_build_pipeline_status`（CC=32）依赖 SQLite 数据库、文件系统扫描、daemon_state 读取等多层依赖，mock 链路长，可能遗漏分支
- **重复 proposal 历史**：此 proposal 已被 pushback 4+ 次，主要因为 BAC 过于宽松（只要求 3 个简单函数）。本次需确保实际覆盖高 CC 函数，否则与已有测试文件无实质差异
- **`_scan_proposal_queue` 内部依赖**：该函数调用 `config.load_config()` 获取 changes_dir，需要 monkeypatch config 返回值

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考（同类 proposal 7 次均未执行到实现阶段）
