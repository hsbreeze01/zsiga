## Verdict: PUSHBACK

## 我的判断

这个 proposal 的核心前提是错的。它声称 `zsiga/harness/runner.py` "缺少测试文件"，要创建 `tests/test_runner.py`。但事实上，`tests/test_harness_runner.py` **已经存在**，包含 277 行代码，全面覆盖了 proposal 中提到的所有 10 个类：`TestEvent`、`TestStarted`、`TestPassed`、`TestFailed`、`TestError`、`HarnessResult`、`TestReport`、`QualificationReport`、`HarnessRunner`（含 `discover()`、`run()`、`run_pytest()`），甚至还有 `_HarnessCollectorPlugin` 的行为验证。静态分析声称"缺少测试文件"是一个明显的遗漏——它在查找 `tests/test_runner.py` 时发现不存在，但没有检查 `tests/test_harness_runner.py`。按照这个 proposal 执行，只会创建一个重复的、低质量的测试文件（只有 `test_module_import` 和 `test_module_smoke`），远不如已有的测试。

## 评分详情
- 可行性: 1/2 -- `zsiga/harness/runner.py` 确实存在，但 proposal 声称模块无测试是**事实错误**。`tests/test_harness_runner.py` 已有 277 行、20+ 个测试用例全面覆盖该模块。
- 可执行性: 1/2 -- 有方向（写测试），但"函数列表"为空（标注"无法提取函数列表"），没有具体的测试用例设计。Technical Design 只写了一般性原则，没有针对具体类/方法的测试策略。
- 能力匹配: 1/2 -- 无近期为此模块添加测试的直接成功记录，但也无连续失败。
- 历史风险: 1/2 -- `verify-layer0-with-tests` 曾在 verify 阶段失败（模式: code.unknown），与本 proposal 同属"为模块添加测试"类别，但失败原因不明确，不构成直接阻断。
- 范围合理性: 0/2 -- **核心前提错误**：proposal 基于模块无测试的判断提出工作，但测试已存在。如果执行，将创建一个名为 `tests/test_runner.py` 的低价值文件，与 `tests/test_harness_runner.py` 形成冗余。此外，BAC 要求的 `test_module_import` 和 `test_module_smoke` 属于最低质量门槛测试，远不如已有覆盖。
- 验收可测性: 2/2 -- 有 4 条 BAC，格式规范（文件存在、符号存在、pytest 退出码 0），均可自动验证。
- 总分: 6/12

## 疑虑
1. **测试已存在，proposal 前提不成立**：`tests/test_harness_runner.py`（277 行）已全面覆盖 `runner.py` 的全部 10 个类，包括事件 dataclass 验证、`discover()` 目录扫描、`run()` 执行与事件收集、`run_pytest()` fail-closed 行为、`QualificationReport` 和 `TestReport` 字段验证。静态分析只检查了 `tests/test_runner.py` 是否存在，遗漏了 `tests/test_harness_runner.py`。
2. **BAC 质量门槛过低**：即使创建 `tests/test_runner.py`，BAC 只要求 `test_module_import`（能 import）和 `test_module_smoke`（冒烟测试），这远低于已有覆盖，等于创建了技术债务。

## 建议
1. **废弃此 proposal**，改为将 `zsiga/harness/runner.py` 标记为"已有测试覆盖"。
2. 如果自演进引擎确实要检测缺失测试的模块，应改进检测逻辑：不仅检查 `tests/test_{module_name}.py`，还要搜索包含该模块 import 的其他测试文件（如 `tests/test_harness_runner.py` 对应 `harness/runner.py`）。
3. 若确实存在覆盖盲区，应先运行 `pytest --cov=zsiga.harness.runner tests/test_harness_runner.py` 获取覆盖率报告，基于具体未覆盖行编写针对性测试。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — "review error and adjust approach"，同类"为模块补测试"任务曾失败，模式: code.unknown
