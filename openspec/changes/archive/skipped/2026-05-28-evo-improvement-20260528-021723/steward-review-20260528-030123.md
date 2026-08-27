## Verdict: PUSHBACK

## 我的判断

我必须驳回这个 proposal。它的核心前提是**错误的**——proposal 声称 `zsiga/duration_predictor.py` 是"无测试模块"，但事实是 `tests/test_phase_duration.py`（241行）已经对该模块进行了**大量测试**，包括直接导入 `_fit_linear` 和 `predict_change_duration`，并覆盖了充分数据、不足数据、负值钳制、缺失阶段键等多个场景。Proposal 的静态分析只检查了 `tests/test_duration_predictor.py` 是否存在，却忽略了同目录下的 `test_phase_duration.py` 已经在测这个模块。基于错误前提提出的方案，即使结构良好，执行后也会产生大量重复测试，浪费 pipeline 资源。

## 评分详情
- 可行性: 2/2 -- 目标模块 `zsiga/duration_predictor.py` 确认存在，5个函数全部验证，接口清晰
- 可执行性: 2/2 -- 有明确的文件名、函数列表、技术设计和 4 条 BAC，结构优秀
- 能力匹配: 1/2 -- 无近期同类"为模块补测试"任务的成功/失败记录，不确定因素
- 历史风险: 1/2 -- auto-generated proposal（"此 proposal 由 zsiga 自演进引擎生成"），触发 -1 规则；无直接相关的重复失败
- 范围合理性: 1/2 -- 范围本身小且独立，但**问题陈述基于错误事实**（"无测试模块"），可能导致创建与 `test_phase_duration.py` 重复的测试
- 验收可测性: 2/2 -- 4 条 BAC 格式规范，`tests/test_duration_predictor.py` 存在性、函数名、test_ 前缀函数数、pytest 退出码均可自动验证
- 总分: 9/12

## 疑虑
1. **核心前提不成立**：proposal 说 `zsiga/duration_predictor.py` "缺少测试文件"，但 `tests/test_phase_duration.py` 已有 241 行测试代码，直接导入并测试了 `_fit_linear` 和 `predict_change_duration`，覆盖了充分/不足数据、负值钳制、缺失键等场景。静态分析只按文件名匹配 `test_duration_predictor.py`，遗漏了实际存在的测试文件。

2. **潜在重复劳动**：如果按 proposal 执行，新建 `test_duration_predictor.py` 将与 `test_phase_duration.py` 中已有的 `TestFitLinear`、`TestPredictChangeDurationSufficient`、`TestPredictChangeDurationInsufficient`、`TestNegativeClamping`、`TestMissingPhaseKeys` 产生大量重复。

3. **未覆盖的函数确实存在但 proposal 未精准定位**：`_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个内部函数在现有测试中没有直接的独立测试（只通过 `predict_change_duration` 间接覆盖），但 proposal 未将这一发现作为重点。

## 建议
1. **修正问题陈述**：承认 `tests/test_phase_duration.py` 已有覆盖，重新定义 problem 为"补充 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的直接单元测试"
2. **选择正确策略**：要么在现有 `test_phase_duration.py` 中追加测试类，要么新建 `test_duration_predictor.py` 但明确只覆盖当前未直接测试的函数，避免与已有测试重复
3. **更新 BAC**：将 BAC-02 中的测试函数名调整为真正需要新增的函数（如 `test__collect_known_phases`、`test__predict_phase`、`test__fallback_estimates`），而非与现有测试重复的 `_fit_linear`

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — review error and adjust approach
