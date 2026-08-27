## Verdict: PUSHBACK

## 我的判断

这个 proposal 的方向没有问题——给 `runner.py` 加测试是合理的——但 proposal 本身质量太差，像一份没填完的模板。静态分析声称"0 函数、无法提取函数列表"，但我一眼就看到 `HarnessRunner` 有 `discover()`, `run()`, `_run_file()`, `run_pytest()` 等方法，还有 `_HarnessCollectorPlugin` 里的 pytest hooks。BAC-02 写的是 `test_(待分析)`——字面意思就是"待分析"的占位符；BAC-03 要求"至少 0 个测试函数"，等于没提任何要求。这不是一个可以放心交给执行者的 proposal。我拒绝在当前状态下批准它。

## 评分详情
- 可行性: 2/2 -- 目标文件 `zsiga/harness/runner.py` 确认存在（317行），含 10 个类，结构清晰。`tests/test_runner.py` 确认不存在，需新建。模块可测性强。
- 可执行性: 1/2 -- 有方向（"为公开函数编写测试"）但缺乏具体路径。声称要 mock "LLM 调用、subprocess" 但模块实际用的是 `importlib.util`、`pytest.main()`、`json`、`time`——对外部依赖的描述不准确。函数列表标注"(无法提取)"，但 `HarnessRunner` 的 `discover()`、`run()`、`run_pytest()` 等方法分明存在且可测。
- 能力匹配: 1/2 -- 无近期同类任务的明确成功记录。历史上有 `verify-layer0-with-tests` 的失败案例。
- 历史风险: 1/2 -- 有相关失败记录 `verify-layer0-with-tests at verify`，但不是完全相同的任务。proposal 自称"由自演进引擎生成"，质量偏低可能重复同样的问题。
- 范围合理性: 2/2 -- 范围清晰：只创建 `tests/test_runner.py`，不修改源码。独立、可逆、低风险。
- 验收可测性: 1/2 -- 有 4 条 BAC，但 BAC-02 `test_(待分析)` 是占位符（不是合法函数名），BAC-03 "至少 0 个 def test_" 阈值为零、无意义。仅 BAC-01 和 BAC-04 可实际验证。不满足"≥3 条有效 BAC 覆盖所有 spec"的标准。
- **总分: 8/12**

## 疑虑

1. **BAC 形同虚设**：BAC-02 写 `test_(待分析)`，这是占位符不是函数名；BAC-03 要求 ≥0 个测试函数——零也能通过。4 条 BAC 中只有 2 条有实际验证能力。执行者可以创建一个空的 `tests/test_runner.py` 就满足 3/4 条 BAC。

2. **静态分析严重不完整**：proposal 声称"0 函数、无法提取函数列表"，但 `HarnessRunner` 明确有 `discover()`（L80）、`run()`（L95）、`run_pytest()`（L169），`_HarnessCollectorPlugin` 有 `pytest_runtest_logstart()`（L271）、`pytest_runtest_logreport()`（L275）。类结构也只列了前 5 个 dataclass，遗漏了 `HarnessResult`、`TestReport`、`QualificationReport`、`HarnessRunner`、`_HarnessCollectorPlugin`。

3. **外部依赖描述错误**：Technical Design 提到 "mock LLM 调用、文件 I/O、subprocess"，但 `runner.py` 中无任何 LLM 调用或 subprocess。实际需要 mock 的是 `pytest.main()`、`importlib.util.spec_from_file_location`、文件写入（JSONL）。

## 建议

1. **修正 BAC**：
   - BAC-02 改为具体函数名，如 `test_discover_raises_on_missing_dir`、`test_run_collects_passed_events`、`test_run_pytest_returns_reports`（至少 3 个有意义的测试名）
   - BAC-03 阈值改为 ≥5 或 ≥8，与模块实际方法数对应
   - 增加 BAC-05: ` HarnessRunner` 的 `discover()`、`run()`、`run_pytest()` 三个公开方法均有对应测试

2. **补全类结构分析**：重新列出全部 10 个类，特别是 `HarnessRunner` 的方法签名和 `_HarnessCollectorPlugin` 的行为，这样执行者才知道该测什么。

3. **修正外部依赖描述**：将 "LLM 调用、文件 I/O、subprocess" 改为 `pytest.main()`（`run_pytest` 中）、`importlib.util`（`_run_file` 中）、JSONL 文件写入（`_append_jsonl` 中）。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — review error and adjust approach。测试相关任务的失败先例，建议在重新提交前确认测试策略与模块实际接口匹配。
