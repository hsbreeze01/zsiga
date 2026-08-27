## Verdict: PUSHBACK

## 我的判断

这个 proposal 目标清晰且风险可控——为 1056 行的 `daemon.py` 添加测试覆盖是必要的。但我对执行细节有顾虑：proposal 列出了函数签名和高复杂度指标，却只给出了"使用 mock 隔离"这样泛泛的技术方向。特别是 `daemon_loop`（CC=38，258行）和 `_build_pipeline_status`（CC=32）这两个怪物函数，没有说明如何构造测试场景、需要 mock 哪些外部状态、如何覆盖关键分支。考虑到 daemon 模块近期有 cycle_error 反复失败的历史，我要求补充更具体的测试策略后再执行。

## 评分详情
- 可行性: 2/2 -- `zsiga/daemon.py` 确认存在（1056行），所有目标函数（`_lock_path`, `_read_daemon_state`, `_scan_proposal_queue` 等）均在代码中定义
- 可执行性: 1/2 -- 有函数列表和优先级，但缺乏具体测试场景设计。例如 `daemon_loop`(CC=38, 258行) 需要如何 mock？哪些分支必须覆盖？没有说明
- 能力匹配: 1/2 -- 无明确的同类任务成功记录。历史中有 `verify-layer0-with-tests` 失败案例
- 历史风险: 1/2 -- daemon.cycle_error 反复出现（5月27日连续3次），`verify-layer0-with-tests` 在 verify 阶段失败过。虽非完全相同的失败模式，但关联度高
- 范围合理性: 2/2 -- 范围清晰：只为 daemon.py 添加测试，不修改源码，不涉及 pipeline 自身
- 验收可测性: 2/2 -- 有 4 条 BAC，格式正确，均可自动验证（文件存在、符号存在、pytest 退出码 0）
- 总分: 9/12

## 疑虑
1. **高复杂度函数的测试策略缺失** -- `daemon_loop`(CC=38, L799-L1056, 258行) 是最复杂的函数，proposal 将其列为优先覆盖目标，但没有说明如何为 38 个分支设计测试用例。这个函数涉及状态机转换、文件 I/O、subprocess 调用、LLM 交互等多重依赖，mock 策略不明确。

2. **daemon 循环失败的历史风险** -- 历史教训显示 daemon.cycle_error 在 5月27日连续出现 3 次（模式：evolution.fix.daemon.cycle_error），5月26日还有 duplicate column name 错误。这表明 daemon 模块的状态管理本身就不稳定，测试时如果 mock 不精确可能掩盖真实问题。

3. **测试覆盖的深度问题** -- AC 只要求"至少 3 个 test_ 函数"和"pytest 退出码 0"，这意味着可以只测试 `_lock_path`、`_daemon_state_path`、`_read_daemon_state` 这三个简单函数（共19行代码）就满足 AC，完全避开高复杂度函数。

## 建议
1. **补充测试矩阵** -- 为高复杂度函数列出具体的测试场景，例如：
   - `_scan_proposal_queue`: 正常队列、空队列、损坏的 proposal 文件、并发写入场景
   - `daemon_loop`: 空闲循环、处理单个 change、连续错误恢复、锁竞争
   - 至少说明每个高 CC 函数需要覆盖的 3-5 个关键分支

2. **强化 AC 的覆盖要求** -- 建议增加：
   - [BAC-05] 至少覆盖 1 个 CC>15 的函数（如 `daemon_loop` 或 `_build_pipeline_status`）
   - [BAC-06] 测试文件中存在至少 10 个 `def test_` 函数（与 21 个公开函数的数量匹配）

3. **明确 mock 策略** -- 说明哪些依赖需要 mock（文件系统、数据库、subprocess、LLM），以及使用什么工具（unittest.mock、pytest fixtures、tmp_path 等）

## 历史参考
- FAIL: daemon cycle errors at execution (2026-05-27) -- cycle_error 反复出现 3 次
- FAIL: verify-layer0-with-tests at verify (2026-05-27) -- 测试验证阶段失败
- FAIL: daemon cycle #1 at execution (2026-05-26) -- duplicate column name 错误
