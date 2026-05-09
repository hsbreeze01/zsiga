# L2: Code Architect — 愿景、方案、计划、任务

## 愿景

从 Shell Artisan 升级为 Code Architect。

**L1 是手艺人**——工具原始（bash/grep/cat），靠经验积累和流程纪律交付。
**L2 是架构师**——拥有结构化代码理解（AST）、并行任务分解（sub-agent）、持续作战能力（context compaction）。

核心改变：zsiga 从"用字符串操作代码"进化为"理解代码结构后精准操作"。

## 三大能力

### 1. Context Compaction（上下文压缩）

**问题**：implement 阶段 50 turns，messages 列表无限增长。后半程 system_prompt + 历史 messages 超过 GLM 的有效注意力窗口，模型开始遗忘早期 specs/design，重复读文件、做过的操作再做一遍。

**方案**：
- `agent/loop.py` 的 `run()` 方法中，每轮结束后检查 messages 总字符数
- 超过阈值（默认 60K chars）时，将历史 messages 压缩为一条摘要
- 摘要由 LLM 生成：提取已完成的工作、关键决策、当前进度
- 压缩后 messages = [system_prompt, summary_message, recent_3_messages]
- 保留最近 3 轮不压缩（保持当前工作上下文）

**技术要点**：
- 压缩本身消耗 1 次 LLM 调用，但节省后续所有调用的 prompt tokens
- 阈值可配置（`compaction_threshold` in PipelineConfig）
- 只在 implement 和 fix loop 阶段启用（enrich/verify 轮次少，不需要）

### 2. Sub-agent（子代理并行）

**问题**：单 agent 串行执行所有 task。复杂 change（如 crawler-domain-strategy 改 18 个文件）在 50 turns 内完不成。独立的 task 之间没有依赖关系，完全可以并行。

**方案**：
- `agent/sub_agent.py`：子 agent 工厂，创建独立 AgentLoop + 工具子集
- orchestrator 检测 tasks.md 中可并行的 task 组（同组内串行，不同组可并行）
- 子 agent 只注册必要工具（bash, read_file, write_file, edit_file, search, list_files）
- 子 agent 结果通过 SharedState 或直接返回字符串合并到主 agent
- 并行限制：最多 2 个子 agent 同时运行（避免服务器过载）

**技术要点**：
- 子 agent 共享同一个 transport 连接
- 子 agent 独立计数 turns/tokens，汇总到主 PhaseRecord
- 子 agent 失败不阻塞其他子 agent，失败结果交给主 agent 处理
- fix loop 仍然是主 agent 的职责，不拆给子 agent

### 3. AST Tools（结构化代码工具）

**问题**：L1 的 `search` 工具是 `grep -rn -E`，`edit_file` 是 Python string replace。无法理解代码结构，导致：
- 搜索 `def process` 会匹配注释 `# def process` 和字符串 `"def process"`
- 替换时 old_text 必须全局唯一，无法按语法结构定位
- 无法做"找到所有调用 X 函数的地方"这种精确查询

**方案**：
- 新增 `ast_search` 工具：基于 ast-grep-py，按 AST pattern 搜索
- 新增 `ast_replace` 工具：基于 ast-grep-py，按 AST pattern 替换
- 保留原有 search/edit 工具（非代码文件仍需要）
- 自动探测文件语言（Python/JS/HTML），选择对应 parser

**ast-grep pattern 示例**：
```
# 找所有函数定义
pattern: "def $NAME($$$PARAMS): $$$BODY"

# 找所有 DataFetcher 的方法调用
pattern: "$OBJ.$METHOD($$$ARGS)"
constraints: { OBJ: { regex: "^fetcher$" } }

# 替换 print 为 logger
pattern: "print($MSG)"
rewrite: "logger.info($MSG)"
```

**技术要点**：
- 依赖：`pip install ast-grep-py`（自带 tree-sitter，无需单独装）
- 远程执行：AST 工具在本地解析，通过 transport 读文件内容后本地处理
- 语言支持：Python、JavaScript、TypeScript、HTML（后续可扩展）
- LLM 自动选择：简单文本操作用 edit_file，代码结构操作用 ast_replace

## 计划（执行顺序）

按收益/风险排序：

| Phase | 能力 | 收益 | 风险 | 预估 |
|-------|------|------|------|------|
| Phase A | Context Compaction | 最高（解决 token 爆炸） | 最低（纯 agent loop 内部改动） | 1-2 天 |
| Phase B | AST Tools | 高（提升代码理解精度） | 中（新增依赖、远程文件读取） | 2-3 天 |
| Phase C | Sub-agent | 高（复杂任务并行度） | 最高（并发控制、结果合并） | 3-5 天 |

## 任务分解

### Phase A: Context Compaction

- [ ] A.1 新建 `agent/compaction.py`
  - `estimate_message_chars(messages) -> int`
  - `compact_messages(messages, keep_recent=3) -> list`
  - `generate_summary(messages) -> str`（调用 LLM 生成摘要）
- [ ] A.2 修改 `agent/loop.py`
  - `run()` 每轮结束时检查总字符数
  - 超过阈值时调用 `compact_messages()`
  - 摘要消息标记 `role: "assistant"` + 特殊前缀 `[compacted summary]`
- [ ] A.3 修改 `config.py`
  - PipelineConfig 新增 `compaction_threshold: int = 60000`（字符数）
  - PipelineConfig 新增 `compaction_enabled: bool = True`
- [ ] A.4 修改 `zsiga.yaml`
  - pipeline 段新增 compaction 配置项
- [ ] A.5 测试
  - 单元测试：compact_messages 缩减消息数
  - 单元测试：summary 保留关键信息
  - 集成测试：implement 阶段超过阈值时自动压缩
- [ ] A.6 Dashboard 展示
  - Phase table 新增 "Compactions" 列
  - PhaseRecord 新增 `compaction_count` 字段

### Phase B: AST Tools

- [ ] B.1 新增依赖
  - `requirements.txt` 加入 `ast-grep-py>=0.34`
  - 测试本地安装和远程兼容性
- [ ] B.2 新建 `agent/ast_tools.py`
  - `_detect_language(filepath) -> str`（从扩展名推断）
  - `_ast_search(code, pattern, language, constraints=None) -> list[dict]`
  - `_ast_replace(code, pattern, rewrite, language) -> str`
- [ ] B.3 注册新工具
  - `agent/tools.py` 的 `register_tools()` 新增 `ast_search` 和 `ast_replace`
  - ast_search 参数：pattern, path, language, constraints
  - ast_replace 参数：pattern, rewrite, path, language
- [ ] B.4 远程文件支持
  - AST 工具通过 transport 读文件 → 本地解析 → 通过 transport 写回
  - 大文件只解析变更相关部分（按行号范围）
- [ ] B.5 更新 Skills
  - `skills/implement.md` 新增 AST 工具使用指南
  - 引导 LLM 在代码操作场景优先用 ast_search/ast_replace
- [ ] B.6 测试
  - 单元测试：Python 函数搜索、类搜索、调用搜索
  - 单元测试：模式替换（rename function、change signature）
  - 集成测试：zsiga pipeline 中使用 AST 工具完成一个 change

### Phase C: Sub-agent

- [ ] C.1 新建 `agent/sub_agent.py`
  - `create_sub_agent(agent_config, target_path, transport) -> AgentLoop`
  - `run_sub_agent(agent, task_prompt, max_turns) -> SubAgentResult`
  - `SubAgentResult`：content, llm_calls, tool_calls, success
- [ ] C.2 修改 `pipeline/orchestrator.py`
  - 新增 `_detect_parallelizable_tasks(tasks_md) -> list[list[task]]`
  - 新增 `_run_parallel_impl(task_groups) -> list[SubAgentResult]`
  - 主 agent 串行执行有依赖的 task，并行执行独立 task
- [ ] C.3 并发控制
  - `asyncio.Semaphore(2)` 限制并发子 agent 数
  - 共享 transport 连接的线程安全（SSH ControlMaster 是进程级，无需额外锁）
- [ ] C.4 结果合并
  - 子 agent 完成后，主 agent 检查所有变更
  - 运行一次完整 pytest + ruff 验证
  - 失败的子 agent 结果交给主 agent 修复
- [ ] C.5 Metrics 扩展
  - PhaseRecord 新增 `sub_agent_count` 字段
  - Dashboard 显示并行度信息
- [ ] C.6 测试
  - 单元测试：task 依赖分析和分组
  - 单元测试：子 agent 创建和执行
  - 集成测试：包含 2 个独立 task 的 change 并行完成

## 文件变更预估

| 新建 | 修改 |
|------|------|
| `zsiga/agent/compaction.py` | `zsiga/agent/loop.py` |
| `zsiga/agent/ast_tools.py` | `zsiga/agent/tools.py` |
| `zsiga/agent/sub_agent.py` | `zsiga/config.py` |
| | `zsiga/pipeline/orchestrator.py` |
| | `zsiga/metrics/types.py` |
| | `zsiga/metrics/dashboard.py` |
| | `zsiga.yaml` |
| | `requirements.txt` |
| | `skills/implement.md` |

## 成功标准

L2 Code Architect branch 合并到 main 当且仅当：

1. **Context Compaction**：implement 阶段消息超过 60K chars 时自动压缩，后 50% turns 的 token 消耗比 L1 降低 ≥ 30%
2. **AST Tools**：ast_search 准确率 > grep 搜索（无误匹配注释/字符串），ast_replace 零误替换
3. **Sub-agent**：包含 2+ 独立 task 的 change，总执行时间比 L1 串行缩短 ≥ 20%
4. **回归测试**：所有 L1 已有的 24 个 change 的 test/lint 结果不变
5. **新依赖**：仅 `ast-grep-py`，无其他新增依赖
