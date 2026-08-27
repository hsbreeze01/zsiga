## Verdict: PUSHBACK

## 我的判断

这个 proposal 我必须驳回。它声称模块"缺少测试文件"，但事实是 `tests/test_phase_duration.py`（241 行）已经包含了对 `duration_predictor` 模块的 9 个测试用例，覆盖了 `_fit_linear` 和 `predict_change_duration`。proposal 的自动生成引擎做了一个过于简单的"文件名是否存在"检查，没有去发现已有测试文件。创建一个新的 `test_duration_predictor.py` 要么是重复造轮子，要么是往错误的方向努力。

更关键的是，proposal 内部自相矛盾：Scope 声明"覆盖公开函数"，但 BAC-02 要求的 `test__collect_known_phases`、`test__fit_linear`、`test__predict_phase` 测试的都是**私有函数**（下划线前缀）。唯一真正的公开函数只有 `predict_change_duration`，而它已经有充分测试了。

如果真要补覆盖，应该把 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的直接测试加到**已有的** `tests/test_phase_duration.py` 中，而不是另起炉灶。

## 评分详情
- 可行性: 2/2 -- 目标模块 `zsiga/duration_predictor.py` 及全部 5 个函数确认存在，无争议。
- 可执行性: 2/2 -- 有明确的变更文件、函数名列表、具体的 BAC 验收条件，实现路径清晰。
- 能力匹配: 2/2 -- 同一模块已有成功测试记录（`test_phase_duration.py` 241 行，9 个通过的测试）。
- 历史风险: 1/2 -- auto-generated proposal 默认 -1。`verify-layer0-with-tests` 的失败记录虽不完全同类型，但提醒我们要警惕自动化生成的测试 proposal。
- 范围合理性: 0/2 -- **自相矛盾**：Scope 声称"覆盖公开函数"，BAC-02 却要求测试 3 个私有函数（`_collect_known_phases`、`_fit_linear`、`_predict_phase`）。且 proposal 的问题陈述是虚假的——模块已有测试，只是文件名不同。
- 验收可测性: 2/2 -- BAC 结构完整，4 条 Binary Acceptance Checks，含文件存在性、符号存在性、测试数量、pytest 退出码，均可自动验证。
- 总分: 9/12

## 疑虑
1. **问题陈述不成立**：proposal 称"模块缺少测试文件 `tests/test_duration_predictor.py`，是潜在风险点"。但 `tests/test_phase_duration.py` 已包含 9 个针对该模块的测试（`TestFitLinear`、`TestPredictChangeDurationSufficient`、`TestPredictChangeDurationInsufficient`、`TestNegativeClamping`、`TestMissingPhaseKeys`）。风险被夸大了。
2. **公开/私有矛盾**：Scope 写"覆盖公开函数"，但 5 个函数中 4 个是私有函数（`_` 前缀），BAC-02 要求的 3 个测试名全部针对私有函数。唯一公开函数 `predict_change_duration` 已有 6 个测试覆盖。
3. **重复建设风险**：如果新建 `tests/test_duration_predictor.py`，将出现两个文件测试同一个模块的局面，增加维护成本，且无实际收益。

## 建议
1. **将补充测试合并到已有文件**：把 proposal 中真正有价值的部分——`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的直接单元测试——添加到 `tests/test_phase_duration.py` 中。这 3 个函数目前仅通过 `predict_change_duration` 间接测试。
2. **修正问题陈述**：proposal 应说明"模块在 `test_phase_duration.py` 中有间接覆盖，但 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 缺少直接测试"，而非虚假声称"缺少测试文件"。
3. **修正 Scope 描述**：改为"为 `duration_predictor.py` 中缺少直接测试的私有函数补充单元测试"，消除公开/私有的矛盾。
4. **更新 BAC**：文件目标改为 `tests/test_phase_duration.py`，测试名改为 `test_collect_known_phases_direct`、`test_predict_phase_direct`、`test_fallback_estimates_direct` 等，且 pytest 命令改为运行 `tests/test_phase_duration.py`。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 自动生成 proposal 容易忽略已有上下文，需更仔细的预检
