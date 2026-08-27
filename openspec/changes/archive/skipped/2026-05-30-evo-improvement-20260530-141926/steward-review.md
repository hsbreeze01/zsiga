## Verdict: PUSHBACK

## 我的判断

这个 proposal 我要驳回。它的前提就有问题——声称模块"缺少测试文件"，但实际上 `tests/test_phase_duration.py` 已经有 241 行、13 个测试直接覆盖了 `duration_predictor` 的 `_fit_linear` 和 `predict_change_duration`。如果盲目执行，会创建一个与现有测试大量重复的新文件。proposal 的真正价值在于为 `_collect_known_phases`、`_fallback_estimates`、`_predict_phase` 三个内部函数补充直接测试，但它完全没有意识到这些函数已有间接覆盖，也没有分析缺口到底在哪。自动生成器在这里犯了"只看文件名、不看实际覆盖"的错误。

## 评分详情
- 可行性: 2/2 -- 目标模块 `zsiga/duration_predictor.py` 确认存在，5 个函数全部核实。创建新测试文件技术上毫无障碍。
- 可执行性: 1/2 -- 有 BAC、有函数列表、有设计原则，方向明确。但 proposal 完全忽略了 `tests/test_phase_duration.py` 已有的 13 个测试，BAC-02 要求的 `test__fit_linear` 将与现有 `TestFitLinear`（2 个测试）直接重复。
- 能力匹配: 1/2 -- 无同类任务（为 duration_predictor 加测试）的直接成功记录。唯一的关联历史 `verify-layer0-with-tests` 以失败告终。
- 历史风险: 2/2 -- 无直接相关的失败模式。`verify-layer0-with-tests at verify` 失败原因模糊（`code.unknown`），不构成同类风险。
- 范围合理性: 1/2 -- 核心问题：proposal 声称"模块缺少测试文件"，但 `tests/test_phase_duration.py` 已存在且直接 import 了 `duration_predictor` 的函数并测试。范围描述具有误导性。正确的 scope 应该是"补充三个内部函数的直接单元测试"而非"创建新测试文件"。创建 `tests/test_duration_predictor.py` 将导致两个文件对同一模块的重复覆盖。
- 验收可测性: 2/2 -- 4 条 BAC 格式规范、可自动验证：文件存在、指定函数名存在、至少 3 个 test_ 函数、pytest 退出码 0。
- 总分: 9/12

## 疑虑
1. **前提事实错误**：proposal 说"缺少测试文件 `tests/test_duration_predictor.py`"，暗示模块无测试。但 `tests/test_phase_duration.py` 已经包含 `TestFitLinear`（直接测 `_fit_linear`）、`TestPredictChangeDurationSufficient`（直接测 `predict_change_duration`）、`TestPredictChangeDurationInsufficient`（间接测 `_fallback_estimates`）等 13 个测试。proposal 的"问题陈述"基于不完整的静态分析。
2. **BAC-02 会制造重复**：BAC 要求 `test__fit_linear` 存在，但 `TestFitLinear` 已有 2 个测试直接调用 `_fit_linear`。新建文件会写入冗余测试。
3. **真正的覆盖缺口未识别**：五个函数中，真正缺直接测试的是 `_collect_known_phases`、`_fallback_estimates`、`_predict_phase`。proposal 没有区分"已覆盖"和"未覆盖"，浪费执行者精力。

## 建议
1. **重写 Problem 段**：承认 `tests/test_phase_duration.py` 已有覆盖，明确列出每个函数的覆盖状态（直接/间接/无），将 scope 改为"补充缺失的直接测试"。
2. **二选一方案**：
   - **方案 A（推荐）**：在 `tests/test_phase_duration.py` 中新增 `TestCollectKnownPhases`、`TestFallbackEstimates`、`TestPredictPhase` 三个测试类，补齐缺口。
   - **方案 B**：如果坚持创建新文件，BAC-02 应排除 `test__fit_linear`（已有覆盖），只要求三个真正缺失的函数的直接测试，并说明新文件与 `test_phase_duration.py` 的分工。
3. **更新 BAC**：至少添加一条验证不与现有测试重复的检查，例如 "新文件中不 import 或测试 `_fit_linear`" 或 "新测试覆盖的函数与 `test_phase_duration.py` 不重叠"。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 虽然原因模糊，但提醒我们在涉及"添加测试"类任务时，应先确认现有覆盖状态再行动，而非基于不完整的静态分析盲目创建。
