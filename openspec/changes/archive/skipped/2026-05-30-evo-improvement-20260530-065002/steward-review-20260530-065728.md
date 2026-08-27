## Verdict: PUSHBACK

## 我的判断

这个 proposal 本身质量不错——目标文件存在、符号全部验证通过、BAC 结构清晰可测、scope 精确到只新建一个测试文件不碰源码。但我无法忽视一个关键事实：**Scout 报告这个 proposal 已经被提交了 12 次以上，全部被 skip/archive**。这不是一个"第一次提出的好主意"，而是一个反复循环却从未落地的任务。项目里甚至已经存在多套完整的参考实现（`evo-improvement-20260530-065002/` 下的活跃版本、两份归档版本），却始终没有合并进 `tests/`。在我批准第 13 次尝试之前，我需要看到这次和前 12 次有什么本质不同，以及为什么之前没有成功。

## 评分详情
- 可行性: 2/2 -- `zsiga/transport.py` 存在且所有符号（`Transport`, `LocalTransport`, `SSHTransport`, `create_transport`）均已验证。`tests/test_transport.py` 不存在，目标明确。
- 可执行性: 2/2 -- 有具体的 target files、需要覆盖的函数/类清单、mock 隔离策略（subprocess）、每个方法的测试场景优先级。BAC 列出了具体的测试函数名。
- 能力匹配: 1/2 -- 项目中有大量其他测试文件存在且可运行，说明写测试的能力是具备的。但这个**特定任务**从未成功完成过，没有近期成功记录。
- 历史风险: 0/2 -- 同一 proposal 循环 12+ 次全部 skip/archive，这是典型的 auto-generated cycling 模式。auto-generated proposal 默认 -1。（基准分 1，-1 后为 0）
- 范围合理性: 2/2 -- 范围极其清晰：新建 `tests/test_transport.py`，不修改 `zsiga/transport.py`，不涉及 pipeline 自身代码。
- 验收可测性: 2/2 -- 4 条 BAC 全部结构化且可自动验证：文件存在、函数名存在、pytest 退出码 0。符合 Binary Acceptance Checks 标准。
- 总分: 9/12

## 疑虑
1. **12+ 次循环未落地**：Scout 明确指出此 proposal 已被提出 12 次以上，全部被 skip/archive。项目内已有多套完整参考实现（`openspec/changes/evo-improvement-20260530-065002/tests/` 下 3 个文件、`archive/skipped/` 下 2 套归档版本），但从未合并到主 `tests/` 目录。这说明阻碍点不在技术层面，而在流程层面。如果不解决流程阻塞，第 13 次也只是第 13 次被 skip。

2. **已有参考实现为何未复用**：`evo-improvement-20260530-065002/` 下已有活跃的完整测试实现（覆盖 `create_transport` 工厂函数、Transport 基类 + LocalTransport、SSHTransport 三个文件）。Proposal 没有说明为何不复用这些现成实现、不复用归档版本，而是要重新生成。这增加了重复劳动和再次失败的概率。

3. **`conftest_zsiga.py` 中的 `mock_transport` fixture 与新测试的兼容性**：Analyst 指出已有的 `mock_transport` 不继承 `Transport` 基类，`run_shell` 签名不同。如果新测试试图复用该 fixture 可能产生冲突，proposal 未说明如何处理。

## 建议
1. **明确说明与历史版本的差异**：在 proposal 中补充一段 "为什么这次不同于前 12 次"——是因为 pipeline 变了？执行策略变了？还是直接复用已有的参考实现？如果可以直接将 `evo-improvement-20260530-065002/tests/` 下的 3 个测试文件合并为 `tests/test_transport.py`，请在 Technical Design 中写明复用计划，而不是"为 X 编写测试"这种从零开始的描述。

2. **将参考实现文件列为 source material**：在 Technical Design 中引用具体的已有测试文件路径（如 `openspec/changes/evo-improvement-20260530-065002/tests/test_spec_…_create_transport_factory.py`），让执行者知道可以直接复用而非重写。

3. **补充对 `conftest_zsiga.mock_transport` 的处理策略**：说明新测试是自包含 mock 还是复用/扩展已有 fixture，避免与现有 15 个测试文件的 transport fixture 产生冲突。

## 历史参考
- 此 proposal 循环记录：12+ 次提交，全部 skip/archive（Scout 分析）
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — review error and adjust approach
- 归档版本：`archive/skipped/2026-05-30-evo-improvement-20260530-043915/tests/`、`archive/skipped/2026-05-30-evo-improvement-20260530-054103/tests/`
