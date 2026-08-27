现在我已经掌握了所有必要的事实。让我做出判断。

## Verdict: PUSHBACK

## 我的判断

这个 proposal 在纸面上质量不差——目标函数全部存在、BAC 结构规范、scope 独立干净。但我无法忽视一个压倒性的事实：**这已是第 24 个 `add-tests-daemon` proposal，前 23 个全部在 gate/steward 阶段被拦截，且没有任何一个成功执行过**。上一轮 steward review（05-30 06:01）给出了非常具体的改进建议（添加 Existing Coverage 段、纠正"公开函数"表述、扩展 BAC 覆盖面），但当前版本完全未采纳这些建议。这不是"还没来得及改进"的问题——这是自演进引擎在同一点上机械循环的典型特征。更具体地说，项目里已有 4 个测试文件在覆盖 daemon.py 的不同函数（`test_daemon_state.py`、`test_daemon_cycle_resilience.py`、`test_daemon_scheduling.py`、`test_dashboard_api.py`），而 proposal 对这些现有覆盖只字不提，executor 无法判断 `test_daemon.py` 是补充还是重复。BAC-02 只要求 3 个测试函数覆盖 3 个极其简单的路径函数（`_lock_path`、`_daemon_state_path`、`_read_daemon_state`），对于一个 1110 行、CC 高达 51 的模块来说，这本质上是象征性的。如果不打破这个循环，第 25 个 proposal 也不会不同。

## 评分详情

- **可行性: 2/2** — `zsiga/daemon.py` 存在（1110 行），所有目标函数（`_lock_path`、`_daemon_state_path`、`_read_daemon_state` 等）由确定性事实确认存在。`tests/test_daemon.py` 确认不存在。目标实体完全匹配。
- **可执行性: 2/2** — 有明确的新建文件（`tests/test_daemon.py`）、具体函数名、mock 隔离策略、4 条 BAC。实现路径清晰。
- **能力匹配: 1/2** — 项目有 70+ 测试文件，monkeypatch/tmp_path/mock 均有先例，写测试是已知能力。但 `add-tests-daemon` 类 proposal 从未有成功执行记录（24 次均在 gate 阶段夭折），无执行参考。
- **历史风险: 0/2** — auto-generated proposal 触发 -1 惩罚。基础分 1（无执行失败，但有 24 次同点循环被拒的明确模式）。最终 0/2。`daemon.cycle_error` 在 learnings.jsonl 中出现 4 次，进一步加重风险信号。
- **范围合理性: 2/2** — 只新建测试文件，不修改源码，scope 独立且边界清晰。不修改 pipeline 自身代码。
- **验收可测性: 2/2** — 4 条 BAC 均为 binary check：文件存在、函数名存在、test_ 数量 ≥3、pytest exit 0。格式规范，可自动验证。
- **总分: 9/12**

## 疑虑

1. **24 轮循环未打破，上一轮 feedback 未被采纳**：代码验证确认 openspec archive 中有 24 个 `add-tests-daemon` proposal.md。上一个版本（05-30 06:01）的 steward review 给出了 3 条明确建议——添加 Existing Coverage 段、纠正"公开函数"表述、扩展 BAC 目标函数——当前版本**一条都没有落实**。这是自演进引擎在同一点上机械循环的典型模式，而非渐进式改进。

2. **现有覆盖被完全忽视**：代码验证确认 `tests/test_daemon_state.py`（242 行）、`tests/test_daemon_cycle_resilience.py`（213 行）、`tests/test_daemon_scheduling.py`（421 行）、`tests/test_dashboard_api.py` 均存在。它们已覆盖 `_write_daemon_state`、`daemon_loop` 等核心函数。Proposal 对此只字不提，executor 无法判断新建 `test_daemon.py` 与现有文件的关系——是补充、合并还是会产生重复。

3. **"公开函数"表述与事实不符**：Proposal 声称覆盖"公开函数"，但列出的 21 个函数中仅 `acquire_lock`、`release_lock`、`daemon_loop`、`_build_status_json`、`_build_metrics_json`、`daemon_loop` 少数几个不是 `_` 前缀。这说明静态分析数据被机械搬运，未经语义审查。

4. **BAC-02 覆盖阈值过低**：仅要求 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 三个测试——这三个函数的圈复杂度均 ≤3，行数加起来不到 20 行。对于一个 CC 高达 51 的 `daemon_loop` 和 CC=32 的 `_build_pipeline_status` 所在模块，这种覆盖本质上是象征性的。

## 建议

1. **添加 "Existing Coverage" 段落**：明确列出 `test_daemon_state.py`、`test_daemon_cycle_resilience.py`、`test_daemon_scheduling.py`、`test_dashboard_api.py` 已覆盖的函数，说明 `test_daemon.py` 的定位是补充未被覆盖的工具函数（如 `_lock_path`、`acquire_lock`、`_compute_uptime_seconds`、`_build_metrics_json` 等），避免未来维护碎片化。

2. **扩展 BAC-02 的目标函数列表**：从 3 个扩展到至少 6 个，增加有实质覆盖价值的函数，例如 `test_acquire_lock_release_lock`（文件锁逻辑）、`test__compute_uptime_seconds`（纯计算，可无 mock 测试）、`test__build_metrics_json`。这能让测试不是纯象征性的。

3. **纠正"公开函数"描述**：改为"为 daemon.py 中尚未被现有测试文件覆盖的工具函数编写单元测试"，避免语义矛盾。同时将 `_scan_proposal_queue`（CC=29）和 `_build_pipeline_status`（CC=32）等高复杂度函数明确列为优先目标，而非仅标注在 Technical Design 段。

4. **添加 anti-loop guard**：在 Proposal 的 Constraints 段明确注明"此 proposal 曾被 steward review 拒绝 24 次，本次已采纳以下具体反馈：[列出上述改动]"，打破自演进引擎的机械循环。

## 历史参考
- FAIL: add-tests-daemon at steward (2026-05-27 through 2026-05-30, 24 instances) — 全部在 gate/steward 阶段被 SKIP/PUSHBACK，无一成功执行
- 最近一次: `evo-improvement-20260530-055610` steward review 评分 9/12 PUSHBACK，建议未被当前版本采纳
- FAIL: daemon.cycle_error (2026-05-27 ×4, 2026-05-29) — learnings.jsonl 中记录的 daemon 相关循环错误
