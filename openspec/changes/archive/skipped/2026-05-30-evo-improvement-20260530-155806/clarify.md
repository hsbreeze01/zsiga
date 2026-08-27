# clarify.md — add-tests-daemon

## 需求拆解

### 原始需求
为 `zsiga/daemon.py`（1110 行、21 函数、1 类）创建集中式单元测试文件 `tests/test_daemon.py`，重点覆盖当前 3 个已有测试文件（`test_daemon_state.py`、`test_daemon_cycle_resilience.py`、`test_daemon_scheduling.py`）未直接覆盖的高复杂度核心函数：`_scan_proposal_queue`(CC=29)、`_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20)、`_build_evolution_status`(CC=11)、`_serve_dashboard.do_GET`(CC=16)。

> **重要上下文**：项目已有 3 个 daemon 相关测试文件共 25 个测试函数，主要覆盖辅助函数（state 读写、调度逻辑、错误恢复）。本需求聚焦**增量覆盖**，不重复已有测试。

### 拆解后的子任务

- [ ] 1. **路径与锁工具函数测试** — 覆盖 `_lock_path()`、`_daemon_state_path()`、`_read_daemon_state()`、`acquire_lock()`、`release_lock()`，验证路径拼接逻辑、锁文件创建/释放、状态文件读取的边界情况（文件不存在、损坏 JSON）。涉及文件：`tests/test_daemon.py` 新建。 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 2. **`_scan_proposal_queue` 核心扫描逻辑测试** — 覆盖 CC=29 的目录扫描函数，验证：空目录、多层嵌套 changes 目录、proposal.md 存在/缺失、status 字段解析（active/completed/failed）、排序逻辑、异常目录跳过。使用 `tmp_path` 构造目录树。涉及文件：`tests/test_daemon.py`。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)
- [ ] 3. **状态构建函数测试套件** — 覆盖 `_build_status_json()`、`_build_metrics_json()`、`_compute_uptime_seconds()`、`_write_daemon_state()`，验证 JSON 输出结构、时间计算边界（零值、跨天）、状态字段完整性。涉及文件：`tests/test_daemon.py`。 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 4. **高复杂度 pipeline/evolution 状态构建测试** — 覆盖 `_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20)、`_build_evolution_status`(CC=11)，mock orchestrator 返回值，验证各种 pipeline 状态组合下的输出结构。涉及文件：`tests/test_daemon.py`。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)

## 边界

### IN scope
- 新建 `tests/test_daemon.py`，包含对 `zsiga/daemon.py` 公开及内部函数的直接单元测试
- 覆盖高 CC 函数（`_scan_proposal_queue`、`_build_pipeline_status`、`_build_proposal_detail`、`_build_evolution_status`）的核心分支
- 使用 mock/monkeypatch 隔离外部依赖（文件 I/O、subprocess、时间函数）
- 测试必须独立运行，不依赖运行时环境

### OUT of scope
- **不修改** `zsiga/daemon.py` 源码（包括修复其 2 个 ruff lint 问题：F401 unused `glob`、F541 空 f-string）
- 不重复 `tests/test_daemon_state.py`（10 个测试）、`tests/test_daemon_cycle_resilience.py`（6 个测试）、`tests/test_daemon_scheduling.py`（9 个测试）已有的覆盖
- 不测试 `daemon_loop`（CC=51, 309 行）— 该函数是顶层编排循环，已被间接覆盖且 mock 链过深，ROI 极低
- 不测试 `_serve_dashboard.do_GET`（HTTP handler，需要 HTTP server 集成测试，不适合纯单元测试）

### 依赖的外部条件
- `zsiga/daemon.py` 在目标项目中存在且可 import
- pytest 框架可用（项目已有 `tests/conftest_zsiga.py`）
- `tmp_path` / `monkeypatch` fixture 可用

## 目标

### 成功标准
1. `tests/test_daemon.py` 文件存在且可被 pytest 发现
2. 文件中包含 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state`（满足 BAC-02）
3. 文件中包含至少 **8 个** `def test_` 函数（BAC-02 的 3 个 + 子任务 2/3/4 的至少 5 个），远超 BAC-03 的最低 3 个要求
4. `python -m pytest tests/test_daemon.py` 退出码 0，全部测试通过
5. 新测试与已有 3 个 daemon 测试文件无功能重复

### 验收方式
- `python -m pytest tests/test_daemon.py -v` 全绿，退出码 0
- `ruff check tests/test_daemon.py` 无 lint 错误
- 人工确认无与 `test_daemon_state.py` / `test_daemon_cycle_resilience.py` / `test_daemon_scheduling.py` 重复的测试用例

## 约束

### 不能修改的文件
- `zsiga/daemon.py` — 仅读取分析，不修改
- `tests/test_daemon_state.py` — 已有覆盖，不动
- `tests/test_daemon_cycle_resilience.py` — 已有覆盖，不动
- `tests/test_daemon_scheduling.py` — 已有覆盖，不动

### 项目部署分支
- `main`

### 已知风险
- **proposal 循环风险**：此 proposal 已被自演进引擎生成 24+ 次，全部在 gate 阶段被 SKIP/PUSHBACK。本次需产出足够质量的测试（≥8 个 test 函数、覆盖高 CC 函数），避免再次被拒
- **import 路径不确定性**：`_scan_proposal_queue` 等函数为模块级私有函数（下划线前缀），需确认 `from zsiga.daemon import _scan_proposal_queue` 可行；若不可行需调整测试策略
- **高 CC 函数 mock 链深度**：`_build_pipeline_status`(CC=32) 内部可能调用多个外部函数，mock 链可能较长，需仔细构造 fixture

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考（同类 proposal 从未成功执行）
