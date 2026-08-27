## Verdict: PUSHBACK

## 我的判断

这个 proposal 看似合理——为一个 317 行、10 个类、零测试的模块补测试——但仔细审查后我发现它是一份**伪装成有结构的空壳**。它自己的静态分析就说"无法提取函数列表"，BAC-02 的测试名是字面量 `test_(待分析)`，BAC-03 要求"至少 0 个测试函数"——这三个字面意思就是"我还没想好测什么"。给 runner.py 写测试本身是对的，但这份 proposal 没有完成最基本的思考就提交了。我拒绝让它以这种状态进入执行。

## 评分详情

- 可行性: 2/2 -- `zsiga/harness/runner.py` 存在且包含 10 个类（确定性事实确认），`tests/test_runner.py` 不存在需新建，目标明确。
- 可执行性: 1/2 -- 有方向（新建测试文件、用 mock 隔离 subprocess），但 proposal 自身承认"无法提取函数列表"，没有指定任何具体的测试场景。说"为公开函数编写测试"的同时自己的数据显示 0 个函数、10 个类——连测什么都不知道。
- 能力匹配: 1/2 -- 无近期同类成功记录，也无连续失败。中性。
- 历史风险: 1/2 -- `verify-layer0-with-tests` 曾在 verify 阶段失败，但那是不同模块。无完全相同的失败模式。虽然 proposal 标注为自演进引擎生成，标题不含 auto-metric/auto-fix，不触发额外扣分。
- 范围合理性: 2/2 -- 范围清晰：只新建 `tests/test_runner.py`，明确排除修改 `runner.py` 源码。不涉及 pipeline 自身代码。
- 验收可测性: 1/2 -- 有 4 条 BAC 结构化格式，但实质内容有严重缺陷：BAC-02 的 symbol 是 `test_(待分析)`（占位符，不是真实的测试函数名）；BAC-03 要求"至少 0 个 def test_"，在数学上恒真，等于没有约束。有效的 AC 实际只有 BAC-01（文件存在）和 BAC-04（pytest 退出 0），且 BAC-04 通过一个空的 conftest 也能满足。验收标准形同虚设。
- 总分: 8/12

## 疑虑

1. **BAC 是空壳**：BAC-02 要求 `tests/test_runner.py` 中存在 `test_(待分析)`——`待分析` 不是合法的 Python 标识符，这是一个没完成的占位符。BAC-03 要求"至少 0 个 `def test_`"，零也能通过。这意味着执行者可以创建一个空的或只有 `def test_placeholder(): pass` 的文件就满足所有 AC。这不是验收标准，这是自欺欺人。

2. **测什么都不知道**：proposal 自己的静态分析输出 `函数列表: (无法提取函数列表)`。Technical Design 说"为公开函数编写单元测试"，但数据显示 0 个函数、10 个类（含 `HarnessRunner`、`_HarnessCollectorPlugin` 等复杂类）。连被测目标的方法签名都没列出，执行者无法规划测试策略。

3. **pytest-in-pytest 递归风险未处理**：`_HarnessCollectorPlugin` 实现了 `pytest_collection_modifyitems` 和 `pytest_runtest_logreport` 钩子。在 pytest 中测试 pytest 插件，如果不严格 mock `pytest.Session` 和 `pytest.Item`，极易导致状态污染或无限递归。proposal 仅泛泛提到"使用 mock"，没有针对此风险的任何设计。

4. **事件类（dataclass）的测试价值存疑**：`TestEvent`、`TestStarted`、`TestPassed`、`TestFailed`、`TestError` 这 5 个类都是简单的 dataclass，proposal 中显示 `methods=[]`。为纯数据类写单元测试价值极低，应明确排除或仅做构造验证，但 proposal 没有做这个区分。

## 建议

1. **重写 BAC，给出具体的测试函数名和最小覆盖数**：
   - BAC-02 应替换为具体测试名，如：`tests/test_runner.py` 中存在 `test_harness_runner_collects_tests`、`test_harness_runner_reports_passed`、`test_harness_runner_reports_failed`（至少列举 5-8 个具体测试函数）
   - BAC-03 应改为"至少 8 个 `def test_` 函数"（给出有意义的下限，基于类和方法的分析）
   - 新增 BAC：`tests/test_runner.py` 中引用了 `HarnessRunner`（确保实际测试了核心类）

2. **补充被测类的关键方法列表**：从 `HarnessRunner`（约 L150-260）和 `_HarnessCollectorPlugin`（约 L260-317）中提取公开方法签名，作为测试设计的输入。至少需要覆盖：`run()` 方法的主路径、`pytest_collection_modifyitems` 的过滤逻辑、`pytest_runtest_logreport` 的事件映射。

3. **明确 pytest 插件的 mock 策略**：在 Technical Design 中说明如何构造 `pytest.Item` mock 对象、如何避免 pytest 状态冲突。建议采用 `pytester` fixture 或直接 mock `_HarnessCollectorPlugin` 的方法入参，而非在真实 pytest session 中运行。

4. **排除纯 dataclass 测试**：在 Scope 中明确 `TestEvent` 等 5 个 dataclass 不需要独立测试，聚焦 `HarnessRunner` 和 `_HarnessCollectorPlugin`。

## 历史参考
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 同为"添加测试"类任务，在验证阶段失败。教训是 AC 定义不清晰时，执行结果无法验证。
