## Verdict: PUSHBACK

## 我的判断

这个 proposal 的核心问题陈述存在事实错误。它声称模块 `zsiga/duration_predictor.py` "缺少测试文件"，但实际上 **该模块已经有相当完善的测试**——在 `tests/test_phase_duration.py`（241 行）中。该文件包含 `TestFitLinear`、`TestPredictChangeDurationSufficient`、`TestPredictChangeDurationInsufficient`、`TestNegativeClamping`、`TestMissingPhaseKeys` 共 5 个测试类，覆盖了公开 API `predict_change_duration` 的主要路径，且直接测试了内部函数 `_fit_linear`。如果照此 proposal 执行，会创建一个 **重复的测试文件**，与已有测试大量重叠。这是在浪费 pipeline 的执行预算。

## 评分详情
- 可行性: 2/2 -- 目标文件 `zsiga/duration_predictor.py` 及全部 5 个函数已验证存在，不存在的技术阻碍为零。
- 可执行性: 2/2 -- 提供了明确的变更文件名、函数名列表、BAC 结构清晰，执行路径具体。
- 能力匹配: 1/2 -- 近期无同类"为已有测试的模块再写测试"的成功记录。历史教训 `verify-layer0-with-tests` 模糊不相关。
- 历史风险: 1/2 -- auto-generated proposal（标题含 `add-tests-` 模式，且约束中明确"由 zsiga 自演进引擎生成"），默认 −1。无直接相关失败，基准 2 → 1。
- 范围合理性: 1/2 -- 核心问题：proposal 声称"缺少测试文件"但 `tests/test_phase_duration.py` 已含 7+ 测试方法覆盖该模块。创建 `test_duration_predictor.py` 会与已有测试大面积重叠。只有 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个私有函数缺乏**直接**测试（但通过 `predict_change_duration` 间接覆盖）。
- 验收可测性: 2/2 -- 4 条 BAC 均可自动验证（文件存在、符号存在、test_ 函数计数、pytest 退出码）。
- **总分: 9/12**

## 疑虑
1. **已有测试未被识别，会导致重复劳动。** `tests/test_phase_duration.py`（241 行）已包含完整的 duration_predictor 测试：`TestFitLinear.test_known_coefficients`、`TestPredictChangeDurationSufficient.test_returns_per_phase_estimates_plus_total`、`TestPredictChangeDurationInsufficient.test_fewer_than_3_returns_fallback`、`TestNegativeClamping`、`TestMissingPhaseKeys` 等。新建 `test_duration_predictor.py` 会导致两个文件测试同一模块，增加维护负担。

2. **Proposal 的 Problem 描述基于不完整的静态分析。** 静态分析只检查了 `tests/test_duration_predictor.py` 是否存在，没有搜索其他文件中是否已导入并测试了 `duration_predictor` 的符号。这是自演进引擎的一个盲区。

3. **三个未直接测试的私有函数价值有限。** `_collect_known_phases`（6行）、`_predict_phase`（31行）、`_fallback_estimates`（23行）均为 `_` 前缀的内部函数，且都已通过公开 API `predict_change_duration` 间接覆盖。为其单独建文件的投入产出比不高。

## 建议
1. **修改 Proposal 目标：从"新建测试文件"改为"整合/补充已有测试"。** 明确承认 `tests/test_phase_duration.py` 已有覆盖，将新增测试追加到该文件中（而非新建文件），或将已有测试迁移到 `test_duration_predictor.py` 并补充缺失的直接测试。
2. **缩小范围：只补充 3 个私有函数的直接测试。** 即 `_collect_known_phases`（空输入、正常输入、缺失 phases key）、`_predict_phase`（<3条走中位数、≥3条走回归、负值钳位）、`_fallback_estimates`（空输入返回 `{"_total": 0.0}`、正常输入返回中位数+total 一致性）。这些是 `test_phase_duration.py` 中缺失的。
3. **更新 BAC：** 修改 BAC-01 从"文件存在"改为"在 `tests/test_phase_duration.py` 中新增 N 个 test_ 函数"或"文件 `tests/test_duration_predictor.py` 存在且 `tests/test_phase_duration.py` 中对应测试已迁移"，避免重复覆盖。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 教训: review error and adjust approach。此案例提醒：在没有充分审查已有覆盖的情况下盲目添加验证层，可能导致重复工作或验证逻辑冲突。
