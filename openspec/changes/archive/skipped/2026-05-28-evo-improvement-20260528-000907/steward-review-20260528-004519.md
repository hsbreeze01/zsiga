Now I have a thorough picture. Let me deliver my verdict.

## Verdict: PUSHBACK

## 我的判断

我仔细审查了这个 proposal，它表面看起来合理——为一个大型无测试模块添加测试——但存在一个核心矛盾：**proposal 声称要优先覆盖高复杂度函数（CC>10），但 Acceptance Criteria 只验证三个最简单的工具函数**。更关键的是，这三个函数（`_lock_path`、`_daemon_state_path`、`_read_daemon_state`）**已经在 `test_daemon_state.py` 中被覆盖**（10 个测试），在 `test_daemon_cycle_resilience.py` 中被间接覆盖。daemon.py 已有 5 个测试文件、~40 个测试，覆盖率约 40-45%。新 proposal 没有解释为什么需要一个新的 `test_daemon.py` 而不是扩展现有文件，也没有在 BAC 中真正约束它声称最重要的目标（高 CC 函数）。这不是一个值得投入的 proposal——除非它能解决这个目标-验收的断裂。

## 评分详情
- **可行性: 2/2** — 目标模块 `zsiga/daemon.py` 确认存在（1056 行），所有 21 个函数经代码验证均为真实定义。pytest 基础设施完善，`conftest_zsiga.py` 提供了 fixture 支持。
- **可执行性: 1/2** — 给出了目标文件和函数列表，但 Technical Design 部分过于笼统。对于 `_build_pipeline_status`（CC=32，130+ 行，需要 mock SQLite + 文件系统 + daemon_state）和 `_build_evolution_status`（CC=11，依赖 EvolutionEngine + langfuse + config 全链路）等高难度函数，只说"使用 mock 隔离外部依赖"，没有具体的 mock 策略。更重要的是，BAC 只要求覆盖三个简单函数，与声称的优先级完全脱节。
- **能力匹配: 1/2** — 近期有 `daemon.cycle_error` 的反复失败记录（3 次），且有 `verify-layer0-with-tests` 在 verify 阶段失败的先例。daemon 测试本身已有大量成功记录（5 个测试文件均通过），但新增测试文件的提议与已有覆盖的协调性存疑。
- **历史风险: 1/2** — `daemon.cycle_error` 是运行时故障而非测试编写失败，但 `verify-layer0-with-tests at verify` 的失败模式值得警惕——测试类 proposal 可能在验证阶段因环境或依赖问题失败。proposal 标注为"由 zsiga 自演进引擎生成"，属于 auto-generated 类型。
- **范围合理性: 2/2** — 范围清晰：只创建 `tests/test_daemon.py`，不修改 `zsiga/daemon.py` 源码。独立于 pipeline 代码，无自修改风险。
- **验收可测性: 2/2** — 4 条 BAC 均为 Binary Acceptance Checks：文件存在性（BAC-01）、特定函数名存在（BAC-02）、最少测试数量（BAC-03）、pytest 退出码（BAC-04）。结构化且可自动验证。
- **总分: 9/12**

## 疑虑

1. **BAC 与声称目标严重脱节**：Proposal 正文明确说"优先覆盖高复杂度函数: `_scan_proposal_queue` (CC=29), `_build_pipeline_status` (CC=32), `_build_proposal_detail` (CC=20)"，但 BAC-02 只要求 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 这三个 CC≤2 的简单工具函数。执行者完全可以只写 3 个 trivial test 就满足所有 AC，而完全忽略高 CC 函数——proposal 的核心价值将归零。

2. **与已有测试的大量重叠**：代码验证显示 `test_daemon_state.py` 已有 10 个测试覆盖 `_write_daemon_state` 及间接覆盖 `_daemon_state_path`、`_read_daemon_state`；`test_daemon_cycle_resilience.py` 间接覆盖 `_lock_path`；`test_dashboard_api.py` 有 12 个测试覆盖 `_scan_proposal_queue` 和 `_build_status_json`。BAC-02 要求的三个测试函数本质上是重复劳动。

3. **未解释为什么需要新文件而非扩展现有文件**：已有 5 个 daemon 相关测试文件（`test_daemon_state.py`、`test_daemon_scheduling.py`、`test_daemon_cycle_resilience.py`、`test_dashboard_api.py`、`test_dashboard_queue.py`）。新 proposal 没有论证为什么 `_compute_uptime_seconds`、`_health_check`、`_build_pipeline_status` 等未覆盖函数不能加入 `test_daemon_state.py` 或 `test_dashboard_api.py`。

4. **auto-generated proposal 的循环风险**：Proposal 约束中明确标注"由 zsiga 自演进引擎生成"。历史教训显示 daemon 相关 auto-generated fix（`evolution.fix.daemon.cycle_error`）出现了 3 次重复记录，暗示自演进引擎对 daemon 模块可能存在循环生成倾向。

## 建议

1. **重写 BAC 以对齐高 CC 函数**：将 BAC-02 从测试简单工具函数改为要求覆盖至少 2 个高 CC 函数，例如：
   - `[BAC-02] tests/test_daemon.py 中存在 test__compute_uptime_seconds, test__health_check, test__build_metrics_json`
   - 新增 `[BAC-05] tests/test_daemon.py 中存在至少 1 个覆盖 _build_pipeline_status 的 test_ 函数`

2. **明确聚焦 11 个真正未覆盖的函数**：跳过已有覆盖的 `_lock_path`、`_daemon_state_path`、`_read_daemon_state`、`_write_daemon_state`、`_scan_proposal_queue`、`_build_status_json`、`daemon_loop`、`acquire_lock`、`release_lock`。新测试应专注于 `_compute_uptime_seconds`、`_build_metrics_json`、`_detect_proposal_phase`、`_build_current_json`、`_health_check`、`_build_pipeline_status`、`_build_proposal_stats_json`、`_build_proposal_detail`、`_build_budget_analysis_json`、`_build_langfuse_summary`、`_build_evolution_status`。

3. **论证文件结构决策**：解释为什么这 11 个函数的测试放在新文件 `test_daemon.py` 而非 `test_daemon_state.py`（已测 state 相关）或 `test_dashboard_api.py`（已测 API 构建）。如果理由是"统一 daemon 模块测试入口"，需要说明未来是否合并现有 5 个文件。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 测试类 proposal 在验证阶段失败的先例
- RECURRING: evolution.fix.daemon.cycle_error (2026-05-27, x3) — daemon 相关 auto-generated proposal 循环生成的模式
