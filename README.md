# zsiga

基于 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 的自主开发智能体。读取目标项目中的需求提案，自动补全规格、实现代码、验证质量，完成 git 提交。

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

# 或安装后直接用
zsiga
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
├── skills/                     # Agent 行为约束
│   ├── enrich.md               #   补全规则
│   ├── implement.md            #   实现规则
│   ├── verify.md               #   验证规则
│   └── safety.md               #   安全红线
├── memory/                     # Agent 记忆
│   ├── active_context.md       #   当前上下文
│   └── learnings.jsonl         #   经验归档
├── templates/                  # 模板（预留）
└── zsiga/                      # 源码
    ├── __init__.py
    ├── __main__.py              # 入口：python -m zsiga
    ├── config.py                # 配置加载
    ├── git_ops.py               # Git 操作
    ├── agent/
    │   ├── loop.py              #   LLM Agent Loop（GLM function calling）
    │   └── tools.py             #   6 个工具（bash, read/write/edit, search, list）
    ├── intake/
    │   └── scanner.py           #   目录扫描，发现 proposal
    └── pipeline/
        ├── orchestrator.py      #   四阶段编排器
        ├── enricher.py          #   Phase 1: 补全
        ├── implementer.py       #   Phase 2: 实现
        ├── verifier.py          #   Phase 3: 验证
        └── utils.py             #   机械化验证 + 归档
```

## Agent 工具

zsiga 为 LLM 注册 6 个工具，全部指向**目标项目**：

| 工具 | 作用 |
|------|------|
| `bash` | 在目标项目目录执行 shell 命令 |
| `read_file` | 读取目标项目文件 |
| `write_file` | 在目标项目创建/覆盖文件 |
| `edit_file` | 精确替换文件中的文本片段（old_text 必须唯一匹配） |
| `search` | 正则搜索目标项目文件内容 |
| `list_files` | 列出目标项目目录结构 |

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
