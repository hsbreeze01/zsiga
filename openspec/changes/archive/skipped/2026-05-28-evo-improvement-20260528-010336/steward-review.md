## Verdict: PUSHBACK

## 我的判断

这个 proposal 的意图是正确的——`runner.py` 确实有 317 行、10 个类、多个公开方法值得测试。但它的 Acceptance Criteria 是一场灾难：BAC-02 用了字面占位符 `test_(待分析)`，BAC-03 要求"至少 0 个 test 函数"——一个空文件就能通过所有四条 BAC。这意味着执行者可以创建一个空的 `tests/test_runner.py`，pytest 退出码 0，所有 AC 全绿，但实际测试覆盖率为零。这是 auto-generated proposal 的典型陷阱：框架正确但内容空洞。我拒绝为这种质量的 proposal 开绿灯。

## 评分详情
- **可行性: 2/2** — `zsiga/harness/runner.py` 确认存在（317 行），含 `HarnessRunner`（含 `discover`/`run`/`run_pytest`/`_run_file` 等方法）、5 个 Event dataclass、`HarnessResult`、`TestReport`、`QualificationReport`、`_HarnessCollectorPlugin`——公开 API 清晰，完全可测试。项目中已有大量 test 文件（`test_ast_tools.py`, `test_daemon_state.py` 等），测试基础设施完备。
- **可执行性: 1/2** — 方向正确（为 runner.py 添加测试），Target Files 明确（新建 `tests/test_runner.py`），但 Technical Design 只说"为公开函数编写单元测试"——而该模块 0 个独立函数，全是类方法。缺乏对具体测试场景的规划（如 `discover` 对不存在目录应抛 `FileNotFoundError`、`run` 对空 test_files 应返回全零 `HarnessResult`、`_run_file` 应正确捕获 `AssertionError` vs 其他 `Exception`）。
- **能力匹配: 1/2** — 无针对此模块的历史记录。项目有丰富的测试编写历史，但无 runner.py 的直接先例。
- **历史风险: 0/2** — `verify-layer0-with-tests` 在 verify 阶段失败（模式：code.unknown），且此 proposal 明确声明由"zsiga 自演进引擎生成"，属于 auto-generated proposal，历史风险 -1。叠加相关失败记录，给 0 分。
- **范围合理性: 2/2** — 范围清晰独立：只新建 `tests/test_runner.py`，不修改 `runner.py` 源码，不影响 pipeline 自身。
- **验收可测性: 0/2** — BAC 结构性崩溃：BAC-02 的 `test_(待分析)` 是字面占位符，不是可匹配的 test 函数名；BAC-03 的"至少 0 个 `def test_`"意味着空文件即可满足；BAC-04 要求 pytest 退出码 0，无测试时同样满足。四条 AC 全部可被空文件通过，**等效于无验收标准**。按规则，总分上限锁定为 6。

**总分: 6/12**（受验收可测性=0 上限限制，锁定为 6）

## 疑虑
1. **BAC 是空洞占位符** — BAC-02 `test_(待分析)` 不是可执行的检查项，BAC-03 "至少 0 个"是零门槛。`runner.py` 有 10 个类、多个方法（`discover`, `run`, `run_pytest`, `_run_file`, `pytest_runtest_logreport`, `_append_jsonl`），但 BAC 没有指定任何一个具体的测试场景。代码证据：`HarnessRunner.discover()` L103-L112 应测试正常发现和不存在的目录；`_run_file()` L133-L195 应测试模块加载失败、AssertionError 分支、通用 Exception 分支。
2. **函数列表提取失败** — proposal 自己承认"(无法提取函数列表)"，这意味着静态分析未能识别 `runner.py` 的实际 API。在此情况下生成测试 proposal，就像给一份你看不到的菜单点菜。
3. **auto-generated 循环风险** — proposal 声明由自演进引擎生成，而 `verify-layer0-with-tests` 已在 verify 阶段失败，模式为 `code.unknown`。如果这次 PUSHBACK 后引擎原样重试，将形成循环。

## 建议
1. **重写 BAC，基于实际 API 指定具体测试函数名**。建议至少以下几条：
   - `[BAC-02]` `tests/test_runner.py` 中存在 `def test_discover_finds_test_files`
   - `[BAC-03]` `tests/test_runner.py` 中存在 `def test_discover_raises_for_missing_dir`
   - `[BAC-04]` `tests/test_runner.py` 中存在 `def test_run_returns_harness_result`
   - `[BAC-05]` `tests/test_runner.py` 中存在 `def test_run_file_catches_assertion_error`
   - `[BAC-06]` `tests/test_runner.py` 中存在至少 **5** 个 `def test_` 函数（不是 0）
   - `[BAC-07]` `python -m pytest tests/test_runner.py` 退出码 0
2. **补充 Technical Design** — 列出每个待测试方法的测试场景（正常路径 + 异常路径），特别关注 `HarnessRunner._run_file()` 的三个分支（加载失败→TestError、AssertionError→TestFailed、其他Exception→TestError）和 `_HarnessCollectorPlugin.pytest_runtest_logreport()` 的 passed/failed/error 三状态。
3. **用 mock 隔离 `pytest.main()` 调用** — `run_pytest()` 内部调用 `pytest.main()`，测试时需 mock 避免 subprocess 副作用。

## 历史参考
- **FAIL: verify-layer0-with-tests at verify** (2026-05-27) — 教训: review error and adjust approach。模式: code.unknown。与本次 proposal 同为"添加测试"类任务，verify 阶段失败说明测试质量/正确性不可想当然。
