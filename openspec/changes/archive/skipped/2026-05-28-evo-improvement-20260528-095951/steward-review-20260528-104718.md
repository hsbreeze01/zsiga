## Verdict: PUSHBACK

## 我的判断
这个 proposal 的核心前提有严重问题。它声称 `zsiga/daemon.py` "缺少测试文件"，暗示该模块缺乏测试覆盖。但事实是：代码库中已经存在 **至少 4 个专门测试 daemon.py 函数的测试文件**，总覆盖量超过 1000 行测试代码。proposal 的静态分析完全忽略了已有测试，导致其"问题"描述是误导性的。我不反对为 daemon.py 补充测试，但前提是要先搞清楚**哪些函数真正缺乏覆盖**，而不是基于一个虚假的"零测试"前提去写测试。

## 评分详情
- **可行性: 2/2** — `zsiga/daemon.py` 存在（1077行），所有目标函数经确定性验证均存在，pytest 框架成熟可用。
- **可执行性: 1/2** — 有方向（新建测试文件、mock 隔离），但 BAC 锁定的目标函数 `_lock_path`（6行）、`_daemon_state_path`（4行）、`_read_daemon_state`（9行）都是极简私有辅助函数。真正需要覆盖的高 CC 函数（`_build_pipeline_status` CC=32、`_build_proposal_detail` CC=20）反而没有出现在 BAC 中。方向有但路径失焦。
- **能力匹配: 2/2** — 项目已有大量成功编写 daemon 测试的记录：`test_daemon_state.py`（242行）、`test_daemon_cycle_resilience.py`（213行）、`test_daemon_scheduling.py`（421行）、`test_dashboard_api.py`（177行），质量都很高。
- **历史风险: 1/2** — 历史中存在反复的 `daemon.cycle_error` 演化修复尝试（3次）和 `verify-layer0-with-tests` 在 verify 阶段的失败。虽然不直接关于"写测试"，但暗示 daemon 相关变更存在风险惯性。
- **范围合理性: 1/2** — scope 声明"只添加测试"是清晰的，但 **Problem 部分的描述是误导性的**。声称"模块缺少测试文件"，实际已有 4+ 个测试文件覆盖了 `_write_daemon_state`、`_scan_proposal_queue`、`_build_status_json`、`daemon_loop` 等核心函数。proposal 没有做覆盖缺口分析，可能导致测试重复或无效。
- **验收可测性: 2/2** — BAC-01~04 结构良好，均为二元可自动验证的检查项（文件存在、符号存在、计数阈值、pytest 退出码）。
- **总分: 9/12**

## 疑虑
1. **核心前提虚假** — proposal 声称 `zsiga/daemon.py` "缺少测试文件 `tests/test_daemon.py`，是潜在风险点"。但代码库已有：`test_daemon_state.py`（覆盖 `_write_daemon_state` 10+ 用例）、`test_daemon_cycle_resilience.py`（覆盖 `daemon_loop` 错误隔离）、`test_daemon_scheduling.py`（覆盖 `daemon_loop` 调度策略 15+ 用例）、`test_dashboard_api.py`（覆盖 `_scan_proposal_queue` 和 `_build_status_json`）。"缺少测试"的判断是不成立的。

2. **BAC 目标失焦** — BAC-02 要求 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state`，这三个函数总计不到 20 行代码，逻辑极其简单（返回路径、读 JSON 文件）。而 proposal 自己识别出的高复杂度函数 `_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20)、`_build_evolution_status`(CC=11)、`_serve_dashboard.do_GET`(CC=16) 完全没有出现在 BAC 中。

3. **重复测试风险** — 如果新建 `test_daemon.py` 并测试 `_read_daemon_state`，而 `test_daemon_state.py` 已经通过 `_write_daemon_state` 测试间接验证了状态文件的读写行为，可能产生无意义的重复。

## 建议
1. **重做覆盖缺口分析** — 逐函数比对已有测试文件，明确列出哪些函数/路径真正没有测试覆盖。用 `pytest --cov=zsiga.daemon` 或手动交叉比对来生成覆盖缺口报告，作为 proposal 的事实基础。
2. **将 BAC 目标替换为真正缺乏覆盖的高 CC 函数** — `_build_pipeline_status`(CC=32)、`_build_proposal_detail`(CC=20)、`_build_evolution_status`(CC=11) 应作为 BAC 的首要目标。对于 `_lock_path`、`_daemon_state_path` 这类返回常量路径的 3-6 行函数，测试价值极低，不应作为验收标准。
3. **考虑扩展现有测试文件而非新建** — 如果 `_read_daemon_state` 确实需要直接测试，最自然的归属是扩展现有的 `test_daemon_state.py`，而非新建文件。除非有明确的组织理由（如测试量过大），否则新建 `test_daemon.py` 会与已有 4 个 daemon 测试文件产生命名混淆。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 测试相关的变更在 verify 阶段失败，提示需确保新测试确实能通过且不引入 flaky 行为
- Evolution: daemon.cycle_error (2026-05-27, 3次重复) — daemon 相关修复反复出现，暗示该模块变更需要特别谨慎
