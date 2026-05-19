## Context

zsiga 当前测试覆盖有限（仅 `tests/test_sub_agent.py` 存在 async 标记问题），能力验证依赖人工观察。L5 达成过程中暴露的问题（intent 误分类、budget 不隔离、关键词缺失）都靠手动发现。

zsiga 的代码结构：
- `zsiga/agent/` — 核心 agent 循环、intent router、sub-agent、reviewer、recovery
- `zsiga/pipeline/` — orchestrator、enricher、implementer、verifier
- `zsiga/metrics/` — collector、dashboard、types
- `zsiga/config.py` — 多模型配置（glm-5.1 + glm-4-flash）
- 现有测试框架：pytest + venv，`tests/` 目录

Harness 作为新模块 `zsiga/harness/` 加入，不侵入现有 agent/pipeline 代码，仅通过 import 验证其行为。

## Goals / Non-Goals

**Goals:**
- 为 L5 六大能力各提供 >= 10 个测试用例，覆盖正常 + 边界 + 对抗场景
- 回归测试在每次 change 完成后自动运行，< 30s 完成
- Level qualification 测试独立于量化指标，harness 结果持久化到 metrics DB
- 所有 harness 输出为结构化 JSON，可被外部 agent 消费
- 测试不依赖真实 LLM 调用，用 mock/stub 保证可重复性

**Non-Goals:**
- 不实现 daemon 服务本身（属于另一个 change）
- 不实现 observer 消费端（Sisyphus 侧，后续集成）
- 不修改 L2-L4 的升级标准（只影响 L5+）
- 不做性能基准测试（不在本次 scope）

## Decisions

### D1: 测试框架选型 — pytest

**选择**: pytest + unittest.mock
**替代方案**: unittest 原生、hypothesis（property-based）
**理由**: zsiga 现有测试用 pytest，无需引入新依赖。mock 足以隔离 LLM 调用。

### D2: LLM 隔离策略 — mock client

**选择**: 在测试中 mock `ZaiClient.chat.completions.create`，返回预定义 JSON
**替代方案**: 用真实 LLM + golden snapshot、录制回放
**理由**: 真实 LLM 调用不可重复（temperature > 0、网络延迟）。intent router 的关键词回退路径是确定性的，LLM 路径通过 mock 验证 prompt 构造和 response 解析。

### D3: Harness 输出格式 — JSONL event stream

**选择**: 每个 test result 写入 `harness-results.jsonl`，格式与 event stream 统一
**替代方案**: JUnit XML、自定义 report 格式
**理由**: JSONL 是 event stream 的基础格式，observer 可直接消费。不需要额外解析器。

### D4: 回归触发机制 — orchestrator post-change hook

**选择**: 在 `ZsigaOrchestrator._run_phases` 的 finally 块中调用 `run_regression()`
**替代方案**: git pre-commit hook、CI pipeline、定时任务
**理由**: orchestrator 是 change 生命周期的管理者，在 finally 中触发确保无论成功/失败都跑回归。pre-commit 对 daemon 模式不适用。

### D5: Level qualification 存储 — 复用 metrics DB

**选择**: 在 zsiga.db 中新增 `harness_results` 表，存储 qualification 结果
**替代方案**: 独立 JSON 文件、SQLite 单独 DB
**理由**: 复用现有 metrics 基础设施，dashboard 可直接查询。不增加文件管理复杂度。

## Risks / Trade-offs

- **[Mock 与真实行为的差距]** mock 的 LLM response 可能不代表真实行为 → 定期用真实 LLM 跑一次 snapshot test，校准 mock 数据
- **[回归测试拖慢 pipeline]** 每次增加 30s → harness 用 pytest-xdist 并行，保持 < 30s；如果超过 60s 改为异步执行
- **[测试维护成本]** 随能力增加测试数量增长 → 每个 capability 测试独立，新增能力只需新增测试文件
- **[级别认证的刚性]** harness 失败 = 不升级，可能因测试 bug 阻碍升级 → harness 本身有测试（meta-test），失败时先检查 harness 代码
