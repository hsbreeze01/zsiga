# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1085 行，21 函数，1 类）新建 `tests/test_daemon.py`，聚焦覆盖高圈复杂度（CC>10）函数。已有 3 个测试文件（`test_daemon_state.py` 242L、`test_daemon_scheduling.py` 421L、`test_daemon_cycle_resilience.py` 213L）覆盖了路径函数、状态读写、调度逻辑和循环韧性，但 `_scan_proposal_queue`(CC=29)、`_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20) 等高复杂度函数缺少直接测试。

### 拆解后的子任务

- [ ] 1. **简单工具函数测试**：覆盖 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`，验证路径拼接和 JSON 反序列化（含文件不存在场景）。（预估复杂度：低, 预估 token：~3000）
- [ ] 2. **队列扫描函数测试**：覆盖 `_scan_proposal_queue`(CC=29, 90L)，mock 文件系统，测试空队列、正常队列、损坏 proposal 文件、混合状态过滤等分支。（预估复杂度：高, 预估 token：~8000）
- [ ] 3. **状态构建函数测试**：覆盖 `_build_status_json`、`_build_metrics_json`、`_compute_uptime_seconds`，验证 JSON 结构和计算逻辑。（预估复杂度：中, 预估 token：~4000）
- [ ] 4. **Pipeline/Evolution 状态构建测试**：覆盖 `_build_pipeline_status`(CC=32, 103L)、`_build_proposal_detail`(CC=20, 76L)、`_build_evolution_status`(CC=11, 64L)，mock SQLite 数据库和文件系统，测试多种 change 状态组合。（预估复杂度：高, 预估 token：~10000）

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含 ≥3 个 `def test_` 函数
- 覆盖 BAC 指定的 3 个函数：`_lock_path`、`_daemon_state_path`、`_read_daemon_state`
- 尽可能覆盖高 CC 函数：`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`
- 使用 mock/monkeypatch 隔离文件 I/O、SQLite、subprocess 等外部依赖

### OUT of scope
- 不修改 `zsiga/daemon.py` 源码（包括不修复 L362 F401 和 L948 F541 lint 问题）
-不修改、不移动已有测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`）
- 不覆盖 `daemon_loop`(CC=43, 284L)——该函数已在 `test_daemon_scheduling.py` 和 `test_daemon_cycle_resilience.py` 中有间接覆盖
- 不覆盖 `_serve_dashboard.do_GET`——涉及 HTTP 服务器 mock，复杂度高且收益有限

### 依赖的外部条件
- `zsiga/daemon.py` 当前源码稳定，函数签名不发生变化
- pytest 基础设施可用（`tests/conftest_zsiga.py` 提供 fixture 支持）
- `zsiga/config.py` 的 `load_config()` 可被 monkeypatch 替换
- `zsiga/metrics/db.py` 的数据库操作可被 mock

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且包含 ≥3 个 `def test_` 函数
2. 包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个指定测试
3. `python -m pytest tests/test_daemon.py` 退出码 0
4. `ruff check tests/test_daemon.py` 无错误
5. 至少覆盖 `_scan_proposal_queue` 或 `_build_pipeline_status` 中的一个高 CC 函数

### 验收方式
- `test -f tests/test_daemon.py && grep -c "def test_" tests/test_daemon.py` → ≥3
- `grep -E "def test__lock_path|def test__daemon_state_path|def test__read_daemon_state" tests/test_daemon.py` → 3 行
- `python -m pytest tests/test_daemon.py -x -q` → 退出码 0
- `ruff check tests/test_daemon.py` → 退出码 0

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（只读分析）
- `tests/test_daemon_state.py`
- `tests/test_daemon_scheduling.py`
- `tests/test_daemon_cycle_resilience.py`
- `tests/conftest_zsiga.py`

### 项目部署分支
`main`

### 已知风险
- `daemon_loop` 和 `_serve_dashboard.do_GET` 不在覆盖范围，如果后续有人以"daemon.py 测试覆盖不足"为由再次提交 proposal，需识别本文件和已有 3 个测试文件的覆盖范围
- `_build_pipeline_status`(CC=32) 依赖 SQLite 查询和文件系统扫描，mock 链路较长，可能需要 2-3 轮调试才能稳定通过
- proposal 由自演进引擎生成，历史上有 4 次 pushback/skip 记录，本轮是首次 ACCEPT
- `_scan_proposal_queue` 内部调用 `load_config()`，需确保 mock 覆盖该路径

### 预估 token 消耗
- prompt: ~12000
- completion: ~6000
- 数据来源: 无历史参考（同类 add-tests-daemon proposal 之前未成功执行过）
