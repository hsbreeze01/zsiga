# zsiga

**L1: Shell Artisan** — 基于 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 的自主开发智能体。

> "Shell Artisan" — 手艺人。工具是原始的（bash、grep、cat），靠经验积累和 OpenSpec 流程纪律交付高质量代码。没有结构化代码理解，没有并行分解，但能稳定完成 ENRICH→IMPL→VERIFY→DELIVER 全流程。

## 版本信息

| 项目 | 值 |
|------|-----|
| Branch | `zsiga-l1-shell-artisan` |
| 等级 | L1 (Shell Artisan) |
| LLM | 智谱 AI GLM-5.1 |
| 源文件数 | 25 个 `.py` |
| 首次运行 | 2026-05 |
| License | MIT |

## L1 能力定位

### 擅长什么

| 能力 | 说明 |
|------|------|
| OpenSpec 四阶段流水线 | ENRICH→IMPL→VERIFY→DELIVER 全自动 |
| Shell 级代码操作 | bash、文件读写、grep 搜索、精确文本替换 |
| SSH 远程开发 | ControlMaster 连接复用，直接操作远程服务器上的项目 |
| 自我学习 | 每次运行记录经验教训，自动注入下次运行的 system prompt |
| 成长日记 | 记录表扬、批评、里程碑和"学会了什么" |
| 机械化验证 | pytest + ruff，只检查本轮改动文件 |
| 安全机制 | approval gate、dry run、protected paths、auto revert |
| 指标仪表盘 | HTML dashboard，里程碑进度条，Pop Mart 吉祥物 |

### 6 个工具

zsiga 为 LLM 注册 6 个工具，全部指向**目标项目**（不能操作自身）：

| 工具 | 作用 | 实现方式 |
|------|------|---------|
| `bash` | 执行 shell 命令 | SSH/Local subprocess |
| `read_file` | 读文件 | `cat` via transport |
| `write_file` | 创建/覆盖文件 | `cat >` via transport |
| `edit_file` | 精确文本替换（old_text 必须唯一匹配） | Python string replace |
| `search` | 正则搜索文件内容 | `grep -rn -E` |
| `list_files` | 列出目录结构 | `ls -la` via transport |

### L1 边界（做不到什么）

| 限制 | 影响 | L2 方向 |
|------|------|---------|
| **无 Context Compaction** | 大项目后半程消息超长，模型能力下降 | 消息超阈值时自动摘要压缩 |
| **无 Sub-agent** | 复杂任务单 agent 扛，无法并行 | 子任务派发 + 并行执行 |
| **无 AST 代码理解** | 靠 grep/regex 匹配，无法理解代码结构 | tree-sitter / AST-grep |
| **无并发保护** | cron 重叠可能同时启动两个 pipeline | PID 锁 / 文件锁 |
| **无智能截断** | 工具输出硬切，可能丢失关键信息 | 按结构截断，保留首尾 |

## L1 成长数据

| 指标 | 值 |
|------|-----|
| Pipeline 运行次数 | 25+ |
| 总 change 数 | 24 |
| 成功 change 数 | 19 |
| 成功率 | 75% |
| 覆盖项目 | 5 (factory, compass, dataagent, stockshark, infopublisher) |
| 经验教训 | 22 条 |
| 总 LLM 调用 | 182 次 |
| 总 Token 消耗 | ~2M prompt + 24K completion |
| 总运行时间 | ~2 小时 |

### 已学会的技能

- 检测目标项目 venv/，用 `venv/bin/python -m pytest` 而不是裸 pytest
- d8q 项目都是 systemd 管理的，用 `systemctl restart` 重启服务，不用 nohup
- patchright `sync_playwright` 在 gunicorn fork 下 greenlet 跨线程崩溃，解法是 PID 检测 + lazy 重置
- THS（同花顺）API 替代被封的 eastmoney push2，用 DataFetcher 单例 + TTL cache 做速率控制
- broken test files 用 `pytest.skip(allow_module_level=True)` 做优雅降级

## 里程碑体系

**L1: Shell Artisan（当前）** ✅ 已达成

| 条件 | 目标 | 实际 |
|------|------|------|
| 成功 change | ≥ 10 | 19 ✅ |
| 成功率 | ≥ 70% | 75% ✅ |
| 项目数 | ≥ 3 | 5 ✅ |
| 经验教训 | ≥ 20 | 22 ✅ |

**L2: Code Architect（下一阶段）**

| 条件 | 目标 |
|------|------|
| Context Compaction | 消息自动摘要 |
| Sub-agent | 任务并行分解 |
| AST Tools | 结构化代码理解 |

**L3: Self-Evolver（远期）**

| 条件 | 目标 |
|------|------|
| 成功 change | ≥ 30 |
| 成功率 | ≥ 85% |
| 验证通过率 | ≥ 80% |
| 首次测试通过率 | ≥ 60% |
| 自身代码修改 | zsiga 能改进自己 |

## 工作原理

```
目标项目/openspec/changes/add-xxx/proposal.md   ← 你写这个
                ↓
        ┌───────────────────────────────────────────────┐
        │  zsiga pipeline                               │
        │                                               │
        │  1. ENRICH  — proposal → specs + design + tasks│
        │  2. IMPLEMENT — tasks → 代码 + 测试 + commit   │
        │  3. VERIFY   — specs vs 代码，三维验证          │
        │  4. DELIVER  — tag + push + archive             │
        └───────────────────────────────────────────────┘
                ↓
目标项目/openspec/changes/archive/2026-05-07-add-xxx/  ← 完成后归档
```

zsiga 操作的是**目标项目**（如 d8q），不是自己。所有 OpenSpec artifacts 存放在目标项目里，跟随代码仓库走。

## 安装

```bash
# Python >= 3.10
pip install -r requirements.txt

# 或
pip install zai-sdk pyyaml httpx ruff
```

## 配置

编辑 `zsiga.yaml`：

```yaml
agent:
  name: zsiga
  llm:
    provider: zhipuai
    model: glm-5.1
    api_key: ${ZHIPUAI_API_KEY}       # 从环境变量读取
    base_url: https://open.bigmodel.cn/api/coding/paas/v4
    proxy: http://proxy.example.com:8080  # 可选，公司代理
    max_tokens: 4096
    temperature: 0.3

targets:
  my-project:
    path: /path/to/your/project
    test_cmd: "pytest -x --tb=short"
    lint_cmd: "ruff check ."

intake:
  mode: dir_scan                        # 目前仅支持目录扫描
  dir_scan:
    scan_interval_seconds: 60

pipeline:
  max_changes_per_cycle: 3              # 每轮最多处理几个 change
  fix_attempts: 10                      # 机械化验证失败后最多修几次
  eval_fix_attempts: 3                  # AI 验证失败后最多修几次
  enrich_max_turns: 25                  # enrich 阶段 LLM 最多多少轮工具调用
  enrich_timeout: 600                   # enrich 超时秒数
  impl_max_turns: 30
  impl_timeout: 900
  verify_max_turns: 12
  verify_timeout: 300
  fix_max_turns: 8                      # 修复循环的每轮上限

safety:
  require_approval: true                # 实现前是否需要人工确认
  dry_run: true                         # true = 不执行 git push
  protected_paths:
    - "*/migrations/*"
    - "*/settings/prod*"
    - "*/.env"
  max_files_per_task: 3                 # 每个 task 最多改几个文件
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `ZHIPUAI_API_KEY` | 智谱 AI API Key，必填 |

```bash
export ZHIPUAI_API_KEY="your-api-key-here"
```

## 如何创建需求

在目标项目的 `openspec/changes/` 下创建目录，放入 `proposal.md`：

```
your-project/
  openspec/
    changes/
      add-health-check/           ← change 名称，随意取
        proposal.md               ← 你写这个文件，其余由 zsiga 生成
```

### proposal.md 格式

```markdown
# Proposal: Add Health Check Endpoint

## Summary
一句话描述要做什么。

## Motivation
为什么需要这个功能。

## Expected Behavior
- 预期的具体行为列表
- 越具体越好，zsiga 会据此生成 specs
```

### OpenSpec Change 生命周期

```
你创建 proposal.md
        ↓
zsiga ENRICH 自动生成:
  ├── specs/                  ← Delta specs（行为变更）
  │   └── xxx-endpoint.md     ← ADDED/MODIFIED/REMOVED Requirements + Scenarios
  ├── design.md               ← 技术方案（架构决策、文件列表）
  └── tasks.md                ← 实现清单（- [ ] 格式）
        ↓
zsiga IMPLEMENT 按 tasks 逐个实现
  每个 task 独立 commit: feat: <task 描述>
        ↓
zsiga VERIFY 三维验证
  Completeness: specs 是否全部覆盖
  Correctness:  实现是否满足行为描述
  Coherence:    是否与项目现有模式一致
        ↓
zsiga DELIVER
  git tag + push + archive
        ↓
openspec/changes/archive/2026-05-07-add-health-check/
```

## 运行

```bash
# 确保在 zsiga 项目目录下，或 zsiga.yaml 在当前目录
cd /path/to/zsiga

# 单次运行（处理所有目标项目中待处理的 change）
export ZHIPUAI_API_KEY="your-key"
python3 -m zsiga

# 生成仪表盘
python3 -m zsiga dashboard
# 输出: site/dashboard.html

# 查看指标
python3 -c "
from zsiga.metrics.collector import compute_stats
s = compute_stats()
print(f'Changes: {s[\"total_changes\"]}, Success: {s[\"success_rate_pct\"]}%')
print(f'Projects: {s[\"distinct_projects\"]}, Lessons: {s[\"lessons_learned\"]}')
"
```

## Pipeline 四阶段详解

### Phase 1: ENRICH（补全）

读取 proposal.md，结合目标项目代码，自动生成三个 OpenSpec artifact：

| 文件 | 内容 |
|------|------|
| `specs/*.md` | Delta specs — 用 `## ADDED Requirements` / `## MODIFIED Requirements` / `## REMOVED Requirements` 组织，每个 Requirement 下有 `#### Scenario`（Given/When/Then） |
| `design.md` | 技术方案 — 架构决策、数据流、需要新增/修改的文件列表 |
| `tasks.md` | 实现清单 — `- [ ]` 格式，每个 task 足够小（最多改 3 个文件） |

如果三个文件已存在，跳过此阶段。

### Phase 2: IMPLEMENT（实现）

按 tasks.md 顺序逐个实现：
1. 找到第一个未勾选的 `- [ ]`
2. 读取对应 specs 和 design
3. 读目标项目现有代码，学习模式
4. 写测试 → 写实现 → 运行 pytest + ruff
5. 勾选 `- [x]` → git commit
6. 下一个 task

**机械化验证**：实现完成后自动运行 pytest + ruff。如果失败，进入修复循环（最多 `fix_attempts` 次）。所有修复失败则 `git reset --hard` 回滚。

### Phase 3: VERIFY（验证）

AI 驱动的三维验证：

| 维度 | 检查内容 |
|------|---------|
| Completeness | 每个 ADDED Requirement 是否有代码实现，每个 Scenario 是否被覆盖 |
| Correctness | 实现是否满足 spec 中的行为描述，pytest 是否通过 |
| Coherence | design.md 中的架构决策是否在代码中体现，命名是否与项目一致 |

输出 `verify.md`，Verdict 为 PASS 或 FAIL。FAIL 时进入 eval-fix 循环。

### Phase 4: DELIVER（交付）

```
git add -A
git commit -m "feat(<project>): <change-name>"
git tag -a zsiga-<change-name>
git push origin main --tags     # dry_run=true 时仅打印
```

完成后将 change 目录移动到 `openspec/changes/archive/<date>-<name>/`。

## 记忆系统

### 工作方式

```
每次 change 处理完成（成功或失败）
        ↓
record_outcome() → memory/learnings.jsonl    ← 追加一条经验
        ↓
cycle 结束 → update_active_context()         ← 从 lessons 重新合成 active_context.md
        ↓
下次启动 → load_active_context()             ← 注入到 agent 的每个 system prompt
```

### 经验格式

每条经验记录在 `memory/learnings.jsonl`，包含 `pattern_key`（分类标签）：

```json
{
  "type": "lesson",
  "ts": "2026-05-07T14:30:00",
  "source": "orchestrator",
  "title": "FAIL: add-health-check at verify",
  "context": "project=stockshark, phase=verify",
  "takeaway": "Failed at verify: verifier wastes turns",
  "pattern_key": "pipeline.fail.verify"
}
```

### 自动注入

`memory/active_context.md` 的内容会在每次 pipeline 运行时自动注入到 agent 的 system prompt 前面。这意味着：
- 之前的教训会被 agent 看到，避免重复犯错
- 积累越多经验，agent 越聪明
- 不需要手动修改 prompt

### 手动添加经验

也可以手动记录经验（不需要跑 pipeline）：

```python
from zsiga.memory.learn import record_lesson

record_lesson(
    title="target project uses venv/",
    context="stockshark has venv/bin/python",
    takeaway="detect venv/ first, use venv/bin/python -m pytest",
    pattern_key="tools.venv_detection",
    source="manual",
)
```

## 安全机制

| 机制 | 说明 |
|------|------|
| **Approval gate** | `require_approval: true` 时，实现前需人工确认 |
| **Dry run** | `dry_run: true` 时，git push 只打印不执行 |
| **Protected paths** | 不修改 migrations、生产配置、.env 等 |
| **Max files per task** | 每个 task 最多改 3 个文件，防止大规模改动 |
| **Auto revert** | 验证失败且修复超限时，自动 `git reset --hard` 回滚 |
| **Scoped tools** | Agent 只能操作目标项目，不能修改 zsiga 自身 |

## 项目结构

```
zsiga/
├── zsiga.yaml                  # 全局配置
├── requirements.txt
├── pyproject.toml
├── skills/                     # Agent 行为约束（Markdown prompt 模板）
│   ├── enrich.md               #   补全规则
│   ├── implement.md            #   实现规则
│   ├── verify.md               #   验证规则
│   └── safety.md               #   安全红线
├── memory/                     # Agent 记忆（自我学习）
│   ├── active_context.md       #   注入到每次 agent 运行的上下文
│   ├── learnings.jsonl         #   经验归档（追加写入）
│   └── journal.jsonl           #   成长日记（表扬/批评/里程碑/学会）
├── metrics/                    # 运行时指标数据
│   └── changes.jsonl           #   每次 change 的完整记录
├── site/                       # 生成的静态文件
│   └── dashboard.html          #   指标仪表盘
└── zsiga/                      # 源码
    ├── __init__.py
    ├── __main__.py              # 入口：python3 -m zsiga
    ├── config.py                # 配置加载（YAML + env var）
    ├── git_ops.py               # Git 操作（commit/tag/push/reset）
    ├── transport.py             # Transport 层（Local + SSH ControlMaster）
    ├── agent/
    │   ├── loop.py              #   LLM Agent Loop（GLM function calling）
    │   └── tools.py             #   6 个工具注册
    ├── intake/
    │   └── scanner.py           #   目录扫描，发现 proposal
    ├── memory/
    │   ├── learn.py             #   经验记录
    │   ├── context.py           #   上下文加载与合成
    │   └── journal.py           #   成长日记读写
    ├── metrics/
    │   ├── types.py             #   数据模型 + 里程碑定义
    │   ├── collector.py         #   指标采集与统计
    │   └── dashboard.py         #   HTML 仪表盘 + Pop Mart 吉祥物
    └── pipeline/
        ├── orchestrator.py      #   四阶段编排器 + fix loops
        ├── enricher.py          #   Phase 1: 补全
        ├── implementer.py       #   Phase 2: 实现
        ├── verifier.py          #   Phase 3: 验证
        ├── utils.py             #   机械化验证 + 归档
        └── project_context.py   #   项目上下文预读
```

## 常见问题

### API 超时

检查网络代理。如果公司内网需要代理访问外部 API：

```yaml
agent:
  llm:
    proxy: http://your-proxy:8080
```

### ruff/pytest 找不到

zsiga 会自动探测目标项目的 `venv/` 或 `.venv/`。确保目标项目有虚拟环境且安装了 pytest 和 ruff：

```bash
cd your-project
source venv/bin/activate
pip install pytest ruff
```

### 目标项目已有 lint 错误

zsiga 的机械化验证只检查**本轮改动文件**（基于 git diff），不会因为目标项目已有的 lint 问题而失败。

### 中断后重新运行

pipeline 是幂等的：
- ENRICH：如果 specs/design/tasks 已存在，跳过
- IMPLEMENT：如果 tasks.md 全部已勾选 `- [x]`，不再实现
- 可安全地多次运行

### 指定 Python 版本

zsiga 要求 Python >= 3.10。如果系统默认版本较低：

```bash
python3.11 -m zsiga
```

## 与目标项目的关系

```
zsiga（独立智能体）          目标项目（d8q 等）
┌─────────────────┐        ┌────────────────────────────┐
│ zsiga.yaml      │        │ openspec/                  │
│ zsiga/ (源码)    │───────▶│   changes/                 │
│ skills/         │  读写   │     add-xxx/               │
│ memory/         │        │       proposal.md ← 人写    │
└─────────────────┘        │       specs/     ← zsiga 生成│
                           │       design.md  ← zsiga 生成│
                           │       tasks.md   ← zsiga 生成│
                           │ src/             ← zsiga 修改│
                           │ tests/           ← zsiga 修改│
                           └────────────────────────────┘
```

zsiga 不修改自身代码，所有操作都发生在目标项目上。

## License

MIT
