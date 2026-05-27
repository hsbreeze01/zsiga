## Verdict: PUSHBACK

## 我的判断

这是一个披着结构化外衣的"探索式"proposal。它说"识别代码异味并实施改进"，但本质上等于"去看一下，觉得什么不好就改什么"——这不是一个可判定完成状态的任务。更令我警惕的是，近期有 3 次改进/测试类任务全部在 verify 阶段失败（`code.unknown` 模式），说明这类开放式"改善质量"任务在当前 pipeline 中极易陷入验证困境。我不会放行一个执行时才发现目标、验收时靠主观判断的 proposal。

## 评分详情

- 可行性: 2/2 -- `zsiga/duration_predictor.py` 确认存在（164 行，5 个符号），目标模块明确。
- 可执行性: 1/2 -- 有方向（读源码→找异味→改→加测试），但没有预判具体问题是什么、改哪个函数、改成什么样。所谓"针对性改进"要在执行时才确定，这不是可执行路径，是探索路径。
- 能力匹配: 1/2 -- 无同类任务（explore-then-improve）的成功记录。
- 历史风险: 1/2 -- 近期有 3 次 verify 阶段失败（`evo-improvement-*`、`verify-layer0-with-tests`、`fix-review-verdict-parser`），模式相似（改进+验证），但非完全相同任务。
- 范围合理性: 1/2 -- 限定了 1 个模块且声明"不做大范围重构"，但"识别可优化项"本身是开放式范围，终点不明确。
- 验收可测性: 1/2 -- BAC-01（"完成代码分析"）无法 binary 检查；BAC-02（"实质性改进，非格式化"）"实质性"是主观判断；仅 BAC-03（通过 pytest/ruff）可自动验证。3 条中只有 1 条真正 binary。
- 总分: 7/12

## 疑虑

1. **BAC-01 和 BAC-02 不是真正的 Binary Acceptance Checks。** "完成代码分析"无法用文件存在/符号存在/测试通过来判定。"实质性改进（非格式化）"的"实质性"是主观词——谁来判断？verify 阶段如果失败了，很可能就是因为这个主观性。历史教训 `evo-improvement-20260527-125207 at verify` 已经验证了这一点。
2. **可执行路径缺失：** proposal 没有预判 `duration_predictor.py` 中的具体问题。164 行代码，5 个函数，proposal 在执行前没有假设任何一个函数存在问题。这意味着 executor 的第一步是"阅读源码"——这应该是 scout 或 analyst 的工作，不是 executor 的工作。
3. **自生成 proposal 的循环风险：** proposal 自述"由 zsiga 自演进引擎生成"。如果 engine 持续生成"探索并改进 X"类 proposal，而每次都在 verify 失败，就会形成自愈循环失败。历史记录已有 3 次同类失败。

## 建议

1. **拆分为两个 proposal：**
   - Proposal A（纯探索）：只读 `zsiga/duration_predictor.py`，输出一份具体的代码审查报告，列出每个函数的问题和改进方案。BAC 设为：报告文件存在、包含至少 N 个具体问题条目、每个条目引用具体行号/函数名。
   - Proposal B（执行改进）：基于 Proposal A 的报告，针对 1-2 个已识别的具体问题实施修改。

2. **重写 BAC 为真正的 binary checks：**
   - `[BAC-01]` tests/test_duration_predictor.py 存在且包含至少 3 个 `test_` 前缀函数
   - `[BAC-02]` `pytest tests/test_duration_predictor.py` 返回 exit code 0
   - `[BAC-03]` `ruff check zsiga/duration_predictor.py` 返回 exit code 0
   - 删除"完成代码分析"和"实质性改进"这种无法 binary 验证的条目。

3. **预判具体问题：** 在 proposal 中先说明预期发现的代码异味类型（如"predict_change_duration 可能缺少边界检查"或"_fit_linear 可能未处理空输入"），让执行有明确目标而非漫无目的的探索。

## 历史参考

- FAIL: evo-improvement-20260527-125207 at verify (2026-05-27) — 自演进改进任务，verify 阶段失败，模式 code.unknown
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 测试验证任务，verify 阶段失败，模式 code.unknown
- FAIL: fix-review-verdict-parser at verify (2026-05-26) — 修复类任务，verify 阶段失败，模式 code.unknown
