## Why

zsiga 已达成 L5（Autonomous Engineer），但级别升级依赖纯量化指标（80 changes、88.9% rate）。这些数字不能证明能力真实存在 — "implement search feature" 被误分类为 research、budget reset 坏了导致 VERIFY 每次耗尽、investigate 不在 INVESTIGATION 关键词里 — 这些问题都是在量变积累完成后才被手动发现的。需要一个系统性的行为检测框架（Harness），可重复、客观地验证每项能力，并在代码演化过程中防止退化。

同时，zsiga 即将从 CLI 工具转型为 daemon 服务，需要为外部 observer（Sisyphus 等 peer agent）提供结构化的行为事件输出，支持 peer-to-peer 分析和持续改进。

## What Changes

- 新增 `zsiga/harness/` 包，包含四层测试体系：
  - **Capability Tests**：每个 L5 能力对应一组测试用例，验证逻辑路径正确性
  - **Behavioral Tests**：边界和对抗测试，验证非理想输入下的行为
  - **Regression Runner**：每次 change 后自动运行全量 harness，检测能力退化
  - **Level Qualification**：级别认证测试，量化达标 + harness 全通过才能升级
- 新增 `zsiga harness` CLI 子命令（`run`、`regression`、`qualify`）
- harness 结果作为 event stream 的一部分输出（JSONL），observer 可消费
- 修改 `ZsigaOrchestrator._run_phases` 在 change 完成后触发 regression
- 修改 `zsiga.metrics.dashboard` 展示 harness 通过率和退化历史

## Capabilities

### New Capabilities

- `capability-harness`: 能力单元测试框架 — 每个 L5 能力对应一组测试用例，验证逻辑路径（不依赖真实 LLM），覆盖 intent router、sub-agent dispatch、recovery、parallel pool、self-review、skill evolution 六大能力
- `behavioral-harness`: 行为边界与对抗测试 — budget resilience（phase 隔离、零 budget、compaction 压力）、intent adversarial（消歧、关键词堆砌、中英混合、空输入）、tool error handling
- `regression-runner`: 回归测试执行器 — 每次 change 后自动运行 capability + behavioral tests，结果 emit 为 event stream，失败时生成退化报告，与 orchestrator 集成为 post-change hook
- `level-qualification`: 级别认证测试 — 量化指标达标后运行专属行为测试（如 L5 需通过端到端 implementation、intent accuracy >= 90%、6 种意图全部路由正确、recovery from failure、budget phase isolation），全通过才记录 level snapshot

### Modified Capabilities

- （无现有 spec 需要修改，harness 是全新能力模块）

## Impact

- 新增代码：`zsiga/harness/` 包（~10 个测试模块 + runner + CLI）
- 修改代码：`zsiga/pipeline/orchestrator.py`（post-change hook）、`zsiga/metrics/collector.py`（harness 指标）、`zsiga/metrics/dashboard.py`（harness 展示）
- 新增依赖：无（基于 pytest + 现有 mock 基础设施）
- 对现有流程的影响：level 升级标准从"纯量化"变为"量化 + harness 通过"，可能影响后续 L6 认证流程
- 与 daemon 化的关系：harness event 输出是 daemon event stream 的首批结构化事件，为 observer 集成铺路
