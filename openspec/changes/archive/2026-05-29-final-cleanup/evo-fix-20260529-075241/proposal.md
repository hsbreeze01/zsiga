# fix-daemon.cycle_error-20260529-0752

## Summary
修复反复出现的 pipeline 失败模式 `daemon.cycle_error`（已出现 2 次），通过分析根因并实施确定性修复。

## Problem
模式 `daemon.cycle_error` 在最近运行中反复出现（2 次），导致 pipeline 可靠性下降。

近期案例：
- APIReachLimitError: Error code: 429, with error text {"error":{"code":"1308","message":"Usage limit reached for 5 hour. Your limit will reset at 2026-05-25 19:22:49"}}
- [permanent] OperationalError: duplicate column name: steward_verdict

## Related Learnings
- [2026-05-29] Auto-generating targeted fix for daemon.cycle_error
- [2026-05-28] ## Verdict: PUSHBACK

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
1. **核心前提虚假** — proposal 声称 `zsiga/daemon.py` "缺少测试文件 `tests/test_daemon.py`，是潜在风险点"。但代码库已有：`test_daemon_state.py`（覆盖 `_write_daemon_state` 10+ 用例）、`test_daemon_cycle_resilience.py`（覆盖 `daemon_loop` 错误隔离）、`test_daemon_scheduling.py`（覆盖 `daemon_loop` 调度策略 15+ 用例）、`test_dashboard_api.py`（
- [2026-05-28] ## Verdict: PUSHBACK

## 我的判断

我仔细审查了这个 proposal，发现一个关键事实被忽略了：**daemon.py 已经有 3 个测试文件、共计 876 行测试代码在覆盖它**。`test_daemon_state.py`（242 行）深度测试了 `_write_daemon_state` 的所有分支，`test_daemon_scheduling.py`（421 行）覆盖了 `daemon_loop` 的调度逻辑，`test_daemon_cycle_resilience.py`（213 行）覆盖了循环错误恢复。这个 proposal 声称"缺少测试文件"是一种由静态分析工具造成的误判——它只检查了 `tests/test_daemon.py` 这个精确文件名是否存在，却忽略了同目录下已有的大量覆盖。

更让我不满的是，BAC 要求的三个测试函数 `test__lock_path`、`test__daemon_state_path`、`test__read_daemon_state` 测试的都是极简函数（6 行、4 行、9 行的路径拼接/文件读取逻辑），这种测试价值极低。而 proposal 自己标注的高 CC 函数（`_scan_proposal_queue` CC=29、`_build_pipeline_status` CC=32、`daemon_loop` CC=43）反而是真正需要测试覆盖的，却没有出现在 BAC 里。这意味着 executor 可以写三个 trivial test 通过所有 BAC，但实际上没有增加任何有意义的覆盖率。

## 评分详情
- 可行性: 2/2 -- `zsiga/daemon.py` 存在（1077 行），所有目标函数已确认存在。tests 目录结构完整，已有 95+ 个测试文件，pytest 基础设施健全。
- 可执行性: 1/2 -- 有目标文件和具体函数名，但存在严重信息缺失：（1）未提及已有 3 个 daemon 测试文件共 876 行覆盖；（2）BAC 指向的 3 个函数都是 <10 行的 trivial 函数，而真正高价值的高 CC 函数未被 BAC 覆盖。
- 能力匹配: 1/2 -- 无近期为大型模块添加测试的明确成功记录。历史中有 verify-layer0-with-tests 在 verify 阶段失败的记录。
- 历史风险: 0/2 -- 自动生成 proposal（明确标注"由 zsiga 自演进引擎生成"），应用 -1 惩罚。基础分 1（daemon 相关有重复失败记录 daemon.cycle_error），惩罚后为 0。历史上 verify-layer0-with-tests 也在 verify 阶段失败，说明自动生成的测试 proposal 有失败先例。
- 范围合理性: 2/2 -- 范围清晰：仅创建 `tests/test_daemon.py`，不修改源码。不涉及 pipeline 自身代码。
- 验收可测性: 2/2 -- 4 条 BAC，全部可自动验证（文件存在、符号存在、至少 3 个 test_ 函数、pytest 退出码 0）。格式规范。
- 总分: 8/12

## 疑虑
1. **已有覆盖被完全忽略**: `test_daemon_state.py`(242L) + `test_daemon_scheduling.py`(421L) + `test_daemon_cycle_resilience.py`(213L) = 8


## Technical Design
1. 在 `zsiga/` 中定位触发 `daemon.cycle_error` 的代码路径
2. 分析每次失败的上下文，提取共性根因
3. 实现确定性修复（非 workaround）
4. 添加防御性检查或 guard 防止复发

### Target Files
- 需要在实施阶段通过代码分析确定

## Acceptance Criteria
- [BAC-01] 修复后 `daemon.cycle_error` 模式不再出现于连续 3 次 pipeline 运行
- [BAC-02] 所有现有测试仍然通过
- [BAC-03] 新增至少 1 个针对该失败模式的防御性测试

## Scope
- In scope: 修复 `daemon.cycle_error` 根因，添加防御性检查
- Out of scope: 不重构无关代码

## Risk
- Impact: Medium — 修改 pipeline 相关代码
- Reversibility: git revert 即可
- Blast radius: 失败模式对应的模块

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成
- project=zsiga
