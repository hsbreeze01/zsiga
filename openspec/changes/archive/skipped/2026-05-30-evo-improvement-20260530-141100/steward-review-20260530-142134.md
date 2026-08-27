## Verdict: PUSHBACK

## 我的判断

这个 proposal 我不能直接放行。它犯了一个不可忽视的错误：**声称 `zsiga/duration_predictor.py` "缺少测试文件"，但 `tests/test_phase_duration.py`（241 行）已经用 8 个测试用例直接测试了该模块的 `_fit_linear` 和 `predict_change_duration`**。proposal 对已有覆盖完全视而不见，这使得它的 Problem Statement 建立在一个不完整的事实之上。不过，我承认现有测试确实只覆盖了 5 个函数中的 2 个（`_fit_linear` 和 `predict_change_duration`），另外 3 个内部函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）仅有间接覆盖，`_fit_linear` 的退化分支也确实未测。所以这个 proposal 的方向是有价值的，但前提是它必须正视现有测试、明确增量价值，而不是假装模块"无测试"。

## 评分详情
- 可行性: 2/2 -- 目标模块 `zsiga/duration_predictor.py` 确实存在，5 个函数全部可验证。纯数学模块，仅依赖 `statistics.median`，无外部依赖隔离难度。
- 可执行性: 2/2 -- 提供了具体的文件名 `tests/test_duration_predictor.py`、5 个目标函数名、BAC 中指定了 3 个测试函数名。路径明确。
- 能力匹配: 1/2 -- 无近期同类任务（为 duration_predictor 添加测试）的成功/失败记录可参考。
- 历史风险: 1/2 -- 有 `FAIL: verify-layer0-with-tests at verify` 的模糊记录，但模式不同（verify 阶段失败 vs 添加测试）。不是完全相同的失败。
- 范围合理性: 1/2 -- Scope 写得清楚（只加测试不改源码），但 **proposal 完全忽略了 `tests/test_phase_duration.py` 已有的 241 行覆盖**。这导致范围描述不完整，可能产出大量重复测试。一个声称"模块无测试"的 proposal 如果不先分析已有测试，它的范围界定就是有缺陷的。
- 验收可测性: 2/2 -- 4 条 BAC，格式规范（文件存在、符号存在、数量约束、pytest 退出码），全部可自动验证。
- 总分: 9/12

## 疑虑
1. **已有测试文件被忽略**：`tests/test_phase_duration.py` 已经有 8 个测试用例直接覆盖 `_fit_linear`（2 个）和 `predict_change_duration`（6 个），通过 `from zsiga.duration_predictor import _fit_linear, predict_change_duration` 引入。proposal 声称模块"缺少测试文件"是**不准确**的——它缺少的是*专用*测试文件，而非测试覆盖。
2. **重复风险**：如果不明确排除已有覆盖，新文件很可能重写 `test_known_coefficients`、`test_empty_input`、`test_fewer_than_3_returns_fallback` 等已存在的测试，造成维护负担。
3. **真正的增量价值未量化**：3 个仅间接测试的函数（`_collect_known_phases`、`_predict_phase`、`_fallback_estimates`）和 `_fit_linear` 的退化分支（`|D| < 1e-12` → 返回均值）才是真正的覆盖缺口，但 proposal 没有指出这些。

## 建议
1. **修改 Problem Statement**：承认 `tests/test_phase_duration.py` 已有覆盖，明确定义增量范围——聚焦于 `_collect_known_phases`、`_predict_phase`、`_fallback_estimates` 的直接测试和 `_fit_linear` 退化分支测试。
2. **在 Scope 中明确排除**：声明不重复 `tests/test_phase_duration.py` 已覆盖的场景，或在 BAC 中加一条 `[BAC-05] tests/test_duration_predictor.py 中不包含与 test_phase_duration.py 功能重复的测试`。
3. **更新 BAC-02**：增加 `test__fallback_estimates` 和/或 `test__collect_known_phases`，使其覆盖真正的覆盖缺口，而非仅仅罗列前 3 个函数名。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — "review error and adjust approach"，虽非完全相同场景，但提醒测试相关 proposal 需要在 verify 前充分理解现有覆盖。
