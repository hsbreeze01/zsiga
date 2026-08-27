## Verdict: PUSHBACK

## 我的判断

这个 proposal 的核心前提有硬伤：它声称 `zsiga/duration_predictor.py` 是"无测试模块"，但 `tests/test_phase_duration.py`（241 行）已经直接导入并测试了 5 个函数中的 2 个（`_fit_linear` 和 `predict_change_duration`），共 11 个测试用例。如果按 proposal 原样执行，创建 `tests/test_duration_predictor.py` 并包含 `test__fit_linear` 等测试，会直接与已有测试大面积重复。proposal 甚至在 BAC-02 里明确要求写 `test__fit_linear`——这个函数已经在 `test_phase_duration.py` 的 `TestFitLinear` 类中被覆盖。这不是一个小问题，而是 proposal 分析阶段的盲区。不过，3 个私有函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）确实缺少直接测试，补测试的诉求有合理内核，所以我给出 PUSHBACK 而非 REJECT。

## 评分详情
- 可行性: 2/2 -- 目标模块 `zsiga/duration_predictor.py` 确认存在（164 行，5 函数），所有符号位置与 proposal 描述一致。技术上写测试毫无障碍。
- 可执行性: 2/2 -- 提供了明确的 target files、函数列表、行号范围，BAC 结构化且可自动验证。路径非常具体。
- 能力匹配: 1/2 -- 无近期同类任务（为 duration_predictor 补测试）的成功记录。唯一的历史教训 `verify-layer0-with-tests` 是通用失败，无直接参考价值。
- 历史风险: 1/2 -- 只有一条泛化的历史失败记录（`code.unknown` 模式），不构成强风险信号。但 proposal 由自演进引擎生成，存在循环生成测试 proposal 的倾向，需保持警惕。
- 范围合理性: 1/2 -- 范围表面清晰，但**前提失实**：声称模块"无测试"忽略了 `tests/test_phase_duration.py`（241 行，11+ 测试用例）已覆盖 `_fit_linear` 和 `predict_change_duration`。BAC-02 要求的 `test__fit_linear` 与已有 `TestFitLinear.test_known_coefficients` / `TestFitLinear.test_empty_input` 直接冲突。这不是范围过大的问题，而是范围定义基于错误前提。
- 验收可测性: 2/2 -- 4 条 BAC 全部结构化且可自动验证：文件存在检查、函数名存在检查、`def test_` 计数、pytest 退出码。覆盖了 proposal 的所有 spec 要点。
- 总分: 9/12

## 疑虑
1. **核心前提失实 — 重复测试风险**：`tests/test_phase_duration.py` 已存在 241 行，通过 `from zsiga.duration_predictor import _fit_linear, predict_change_duration` 直接导入，包含 `TestFitLinear`（2 tests）、`TestPredictChangeDurationSufficient`（2 tests）、`TestPredictChangeDurationInsufficient`（3 tests）、`TestNegativeClamping`（1 test）、`TestMissingPhaseKeys`（1 test）。BAC-02 要求写 `test__fit_linear` 将直接与 `TestFitLinear` 重复。proposal 完全没有提及这个已有文件。
2. **实际覆盖缺口与声称不符**：真正的缺口只有 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 三个私有函数缺少直接测试。proposal 应聚焦这 3 个函数，而非声称"5 个函数全部无测试"。

## 建议
1. **修正 proposal 前提**：在 Problem 段落中承认 `tests/test_phase_duration.py` 已存在，明确说明真实的覆盖缺口是 3 个私有函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）。
2. **缩小 scope，避免重复**：将 BAC-02 中的 `test__fit_linear` 替换为 `test__collect_known_phases`、`test__predict_phase`、`test__fallback_estimates`。或者考虑在现有 `tests/test_phase_duration.py` 中追加测试而非创建新文件。也可以坚持创建新文件，但明确只覆盖未被测试的 3 个私有函数。
3. **更新 Summary**：从"为无测试模块添加覆盖"改为"补全 `duration_predictor` 中 3 个未被直接测试的私有函数覆盖"。
