## Verdict: PUSHBACK

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
1. **已有覆盖被完全忽略**: `test_daemon_state.py`(242L) + `test_daemon_scheduling.py`(421L) + `test_daemon_cycle_resilience.py`(213L) = 876 行测试已覆盖 `_write_daemon_state`、`daemon_loop` 调度逻辑、错误恢复。Proposal 声称"缺少测试文件"是误导性的。如果新增 `test_daemon.py`，需要明确说明它与现有 3 个文件的分工边界。
2. **BAC 与设计目标自相矛盾**: Technical Design 明确说"优先覆盖高复杂度函数: `_scan_proposal_queue`, `_build_pipeline_status`, `_build_proposal_detail`"，但 BAC-02 只要求 `test__lock_path`, `test__daemon_state_path`, `test__read_daemon_state`。executor 完全可以只写 trivial test 通过所有 BAC 而忽略高 CC 函数。
3. **高 CC 函数的 mock 复杂度被低估**: `_scan_proposal_queue`(CC=29) 内部调用 `load_config()`、`load_all_changes()` 并做文件系统遍历；`_build_pipeline_status`(CC=32) 依赖 SQLite + 文件系统 + daemon_state。这些函数的 mock 隔离需要精心设计，proposal 没有给出具体的 mock 策略。

## 建议
1. **修订 BAC 以覆盖高价值目标**: 将 BAC-02 改为要求测试高 CC 函数，例如：
   - `tests/test_daemon.py` 中存在 `test__scan_proposal_queue_*`（至少 2 个变体）
   - `tests/test_daemon.py` 中存在 `test__build_pipeline_status_*` 或 `test__build_proposal_detail_*`
   - 保留 `test__read_daemon_state` 作为基础覆盖
   
2. **明确与现有测试的边界**: 在 proposal 中声明 `test_daemon_state.py` 已覆盖 `_write_daemon_state`，`test_daemon_scheduling.py` 已覆盖 `daemon_loop` 调度逻辑，`test_daemon_cycle_resilience.py` 已覆盖错误恢复。新文件专注于：路径工具函数（`_lock_path`, `_daemon_state_path`）、文件读取函数（`_read_daemon_state`）、扫描函数（`_scan_proposal_queue`）、JSON 构建函数（`_build_status_json`, `_build_current_json`）、健康检查（`_health_check`）。

3. **补充 mock 策略说明**: 针对 `_scan_proposal_queue` 需要 mock `load_config` 和 `load_all_changes`；针对 `_build_pipeline_status` 需要 mock SQLite 和文件系统。至少说明用 `tmp_path` + `monkeypatch` 的模式。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 自动生成的测试 proposal 在 verify 阶段失败
- Evolution: identified recurring failure daemon.cycle_error (2026-05-27) — daemon 相关改动有重复失败模式（连续 3 次出现）
