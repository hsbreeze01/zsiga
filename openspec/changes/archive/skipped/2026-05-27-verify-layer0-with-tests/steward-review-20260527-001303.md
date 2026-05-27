## Verdict: PUSHBACK

## 我的判断

这个 proposal 的意图是好的——为 Layer 0 确定性验证体系补充测试覆盖，技术设计也写得很详细。但我必须指出一个致命矛盾：proposal 声称要测试 `verifier.py` 的 `verify()` 函数和 `roles.py` 的 `_STEWARD_PROMPT`，而确定性事实明确显示这两个文件不存在，相关符号也无处可寻。写出来的测试会因 import 失败直接崩掉，BC-01（pytest exit code 0）根本不可能满足。一份声称 "zero risk" 却会让 pytest 全红的测试套件，比没有测试更糟糕——它制造了虚假的安全感。

## 评分详情

- **可行性: 1/2** — `verify_layer0.py`（`run_layer0_checks`@L627, `check_spec_file_coverage`@L159, `write_layer0_verify_md`@L687）、`learn.py`（`record_lesson`@L8, `record_outcome`@L45）、`context.py`（`load_recent_lessons`@L31）均已确认存在。但 `verifier.py` 不存在、`verify()` 无定义、`roles.py` 不存在、`_STEWARD_PROMPT` 无匹配、`PipelineConfig` 的 `proposal_gate_score_accept`/`proposal_gate_score_pushback` 均未找到。29 个测试中约 20 个目标可确认，9 个悬空。

- **可执行性: 2/2** — 每个测试函数都有明确的构造步骤、mock 策略和断言目标。Technical Design 的粒度可以直接转化为代码，这是我见过的最详细的测试 proposal 之一。

- **能力匹配: 1/2** — 无近期同类任务的成败记录可供参考，首次尝试此类规模测试套件的编写。

- **历史风险: 1/2** — 无相关失败记录，但无成功记录。

- **范围合理性: 2/2** — 范围清晰：4 个新建测试文件，不碰生产代码。可逆性极高（删除文件即可）。

- **验收可测性: 2/2** — 15 条 BAC 格式规范（`文件中存在 symbol`），3 条 BC 覆盖行为和工具链。覆盖率完整。

- **总分: 9/12**

## 疑虑

1. **`verifier.py` 幽灵依赖**：proposal test 21-22 要 `import` 并测试 `verifier.py` 的 `verify()` 函数。确定性事实：`verifier.py` ❌ 不存在，`verify` 仅作为字符串 reference 出现在 `zsiga/metrics/collector.py:95`（那只是 phase 名称枚举，不是可调用函数）。tests/test_verifier_layer0_integration.py 会因 ModuleNotFoundError 无法加载，BC-01 必然失败。proposal 自称 "Impact: None" 和 "所有测试用 pytest 执行通过" 自相矛盾。

2. **`roles.py` 和 `_STEWARD_PROMPT` 缺失**：test 26 要 "读取 roles.py 中 _STEWARD_PROMPT"。确定性事实：`roles.py` ❌ 不存在，`_STEWARD_PROMPT` ❌ 无匹配。注意 `_parse_verdict` 实际存在于 `zsiga/pipeline/proposal_gate.py:46`，说明评分逻辑可能在 proposal_gate.py 而非 roles.py。proposal 对模块归属的假设有误。

3. **`PipelineConfig` 属性未确认**：test 29 要验证 `proposal_gate_score_accept=10` 和 `proposal_gate_score_pushback=6`。这两个属性在符号验证中均 ❌ 未找到定义。如果 PipelineConfig 不含这些字段，test 29 的断言就会失败。

## 建议

1. **拆分为两个 proposal**：将 29 个测试按目标模块存在性拆分。
   - **Proposal A（立即可行）**：test 1-20（verify_layer0.py），test 23-25（learn.py/context.py），test 27-28（proposal_gate.py 的 _parse_verdict）。这些目标全部确认存在，可以直接执行。预估 25 个测试，可行性直接升到 2 分。
   -
