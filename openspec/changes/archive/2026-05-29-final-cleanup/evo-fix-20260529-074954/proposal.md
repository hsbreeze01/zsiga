# fix-pipeline.fail.verify.diagnosed-20260529-0749

## Summary
修复反复出现的 pipeline 失败模式 `pipeline.fail.verify.diagnosed`（已出现 3 次），通过分析根因并实施确定性修复。

## Problem
模式 `pipeline.fail.verify.diagnosed` 在最近运行中反复出现（3 次），导致 pipeline 可靠性下降。

近期案例：
- Diagnosed root cause: Missing or incorrect import / dependency. Fix: Best guess: Missing or incorrect import / dependency. Evidence: ImportError
- Diagnosed root cause: Recent code change introduced a regression. Fix: Best guess: Recent code change introduced a regression. Evidence: === REVIEW CRITICAL ===
1. [CRITICAL] No implementation code exists in the change. The git diff is empty and the reposit
- Diagnosed root cause: Recent code change introduced a regression. Fix: Best guess: Recent code change introduced a regression. Evidence: === verify.md ===
Verdict: FAIL
Layer 0: FAIL — 7/8 checks passed

## Failed Checks
1. [CRITICAL] spec_scenario_coverage

## Related Learnings
- [2026-05-29] Auto-generating targeted fix for pipeline.fail.verify.diagnosed
- [2026-05-29] Auto-generating targeted fix for pipeline.fail.verify.diagnosed
- [2026-05-29] ## Verdict: REJECT

## 我的判断

这是一个已经失控的自演进循环的第 N 次迭代，我拒绝为它开绿灯。代码验证显示：`diagnose-recent-failures` 这个 proposal 标题在代码库中出现了 **27 次**（`evolution.py:562` 中甚至硬编码了这个模板字符串），`pipeline.fail.verify.diagnosed` 在 learnings.jsonl 中记录了 **139 条**，而 STEWARD 已经 REJECT 了同名/同模式 proposal **37 次**。上一次 STEWARD 对这个 proposal 的评审（`steward-review-20260527-115332.md`）给了 2/12 分，理由和我要说的一模一样。这个 proposal 本身就是它试图修复的问题的一部分——每一次 REJECT 都会写入一条新的 failure 记录，触发 evolution engine 再生成一个同名 proposal，形成死循环。自演进引擎的 `evolution.py` 需要一个 meta-loop 保护机制：当同一模板连续被 REJECT ≥3 次时，应该停止生成而不是继续。

## 评分详情
- 可行性: 1/2 — 诊断基础设施（`diagnoser.py:462` 的 `diagnose` 函数、`evolution.py` 的 failure 记录）确实存在。但"实施针对性修复"的目标完全未知——不知道要改什么。
- 可执行性: 0/2 — 零具体实现路径。"分析 diagnosis.md → 提取根因 → 实施修复"是流水账式愿望清单，没有指向任何具体的文件、函数或接口。规则明确：只有目标没有路径 = 0。
- 能力匹配: 0/2 — 同名 proposal 连续被 STEWARD REJECT 37 次，成功率 = 0%。近 24 小时内同类任务零成功。
- 历史风险: 0/2 — 完全相同的失败模式刚发生过（37 次），auto-generated proposal 触发 -1 惩罚，基础分 0 封底。learnings.jsonl 中 139 条 `pipeline.fail.verify.diagnosed` 记录是这个循环失控的铁证。
- 范围合理性: 0/2 — scope 写着 `project=zsiga`，即修改 pipeline 自身代码，按规则上限锁定为 1。但更致命的是范围自相矛盾："分析根因"（只读）和"实施修复"（写入）打包在一起，而且 proposal 模板本身就在 `evolution.py:562` 中硬编码生成——这是典型的自指循环。
- 验收可测性: 0/2 — 三条 BAC 没有一条符合 Binary Acceptance Check 格式。"至少分析 2 个"是数量下限非 binary；"对可修复的根因实施修复"主观判定"可修复"；"修复后相关测试通过"未指定哪些测试。触发总分上限锁定为 6。
- 总分: 1/12

## 疑虑
1. **自演进循环完全失控**：`evolution.py:562` 硬编码了 `diagnose-recent-failures` 模板。每次 rejection 都产生新的 failure → evolution engine 再触发同一模板 → 再被 REJECT → 循环。learnings.jsonl 中 139 条同模式记录（2026-05-27T17:05~17:


## Technical Design
1. 在 `zsiga/` 中定位触发 `pipeline.fail.verify.diagnosed` 的代码路径
2. 分析每次失败的上下文，提取共性根因
3. 实现确定性修复（非 workaround）
4. 添加防御性检查或 guard 防止复发

### Target Files
- 需要在实施阶段通过代码分析确定

## Acceptance Criteria
- [BAC-01] 修复后 `pipeline.fail.verify.diagnosed` 模式不再出现于连续 3 次 pipeline 运行
- [BAC-02] 所有现有测试仍然通过
- [BAC-03] 新增至少 1 个针对该失败模式的防御性测试

## Scope
- In scope: 修复 `pipeline.fail.verify.diagnosed` 根因，添加防御性检查
- Out of scope: 不重构无关代码

## Risk
- Impact: Medium — 修改 pipeline 相关代码
- Reversibility: git revert 即可
- Blast radius: 失败模式对应的模块

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成
- project=zsiga
