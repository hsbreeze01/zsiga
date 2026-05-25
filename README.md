# zsiga

自主工程智能体。读取 OpenSpec proposal，自动完成规格补全、代码实现、质量验证、Git 交付的完整 pipeline。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export ZHIPUAI_API_KEY="your-api-key"

# 3. 投递 proposal
mkdir -p openspec/changes/my-feature
cat > openspec/changes/my-feature/proposal.md << 'EOF'
# my-feature
## Summary
一句话描述要做什么。
## Requirements
- 具体需求列表
EOF

# 4. 启动 daemon
python -m zsiga daemon --port=58175

# 5. 监控状态
curl http://localhost:58175/api/pipeline-status
```

## 配置

### zsiga.yaml

```yaml
agent:
  name: zsiga
  llm:
    provider: zhipuai
    model: glm-5.1
    api_key: ${ZHIPUAI_API_KEY}
    base_url: https://open.bigmodel.cn/api/coding/paas/v4
    max_tokens: 4096
    temperature: 0.3

targets:
  my-project:
    path: /path/to/your/project
    test_cmd: "pytest -x --tb=short"
    lint_cmd: "ruff check ."
    deploy_branch: main
    merge_to_branches: []          # DELIVER 后自动 merge 到的额外分支

intake:
  mode: dir_scan
  dir_scan:
    scan_interval_seconds: 60

pipeline:
  cycle_interval_hours: 8         # 主循环间隔
  idle_poll_minutes: 5            # 无 proposal 时的轮询间隔
  max_changes_per_cycle: 3
  enrich_max_turns: 25
  enrich_timeout: 600
  impl_max_turns: 30
  impl_timeout: 900
  design_gate_enabled: true       # Judge 评审 spec 质量
  design_gate_max_retries: 2      # Judge 失败后 ENRICH 重试次数

  proposal_gate:
    enabled: true
    score_accept: 6               # Steward 评分 >= 此值通过
    score_pushback: 3             # < 此值直接拒绝

safety:
  require_approval: false
  dry_run: false
  protected_paths:
    - "*/migrations/*"
    - "*/settings/prod*"
    - "*/.env"
```

### 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `ZHIPUAI_API_KEY` | 智谱 AI API Key | 是 |
| `LANGFUSE_PUBLIC_KEY` | Langfuse 可观测性公钥 | 否 |
| `LANGFUSE_SECRET_KEY` | Langfuse 可观测性密钥 | 否 |
| `LANGFUSE_HOST` | Langfuse 服务地址 | 否 |

### systemd 服务

创建 `/etc/systemd/system/zsiga-daemon.service`：

```ini
[Unit]
Description=zsiga autonomous engineer daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=lancer
Group=lancer
WorkingDirectory=/home/zsiga/repo
EnvironmentFile=/home/zsiga/repo/.zsiga.env
ExecStartPre=/usr/bin/git checkout -f main
ExecStart=/home/zsiga/repo/venv/bin/python -m zsiga daemon --port=58175
Restart=on-failure
RestartSec=60
StandardOutput=journal
StandardError=journal
SyslogIdentifier=zsiga
KillSignal=SIGTERM
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
```

环境文件 `.zsiga.env`（chmod 600，gitignore）：

```bash
ZHIPUAI_API_KEY=your-key-here
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://jp.cloud.langfuse.com
```

### 启停命令

```bash
# systemctl 方式
sudo systemctl enable zsiga-daemon    # 开机自启
sudo systemctl start zsiga-daemon    # 启动
sudo systemctl stop zsiga-daemon     # 停止
sudo systemctl restart zsiga-daemon  # 重启
sudo systemctl status zsiga-daemon   # 查看状态

# 脚本方式（前台运行，日志输出到 stdout）
python -m zsiga daemon --port=58175

# 单次运行（处理完所有 proposal 后退出）
python -m zsiga run
```

### 运行时信号

| 信号 | 效果 |
|------|------|
| `SIGTERM` / `SIGINT` | 完成当前 cycle 后优雅退出 |
| `SIGUSR1` | 暂停（完成当前 cycle 后等待） |
| `SIGUSR2` | 恢复运行 |

```bash
kill -SIGUSR1 $(cat data/lock.pid)   # 暂停
kill -SIGUSR2 $(cat data/lock.pid)   # 恢复
```

## 投递 Proposal

### 目录结构

```
项目根目录/
  openspec/
    changes/
      add-health-check/           ← proposal 名称
        proposal.md               ← 你写这个，其余 zsiga 自动生成
```

### proposal.md 内容要素

```markdown
# proposal-name

## Summary
一句话描述要做什么。必须具体，包含目标文件和功能。

## Problem
为什么需要这个变更。现有系统的什么缺陷或缺失。

## Technical Design
技术方案。包含：
- 要修改的文件列表和函数名
- 数据流和接口设计
- 错误处理策略

## Acceptance Criteria
验收标准。每条必须是可验证的：
1. `curl http://localhost:58175/api/health` 返回 HTTP 200
2. 响应包含 `status` 和 `timestamp` 字段
3. 现有端点不受影响

## Scope
- **In scope**: 明确在范围内的变更
- **Out of scope**: 明确不在范围内的变更

## Risk
- **Impact**: 高/中/低
- **Blast radius**: 影响范围
- **Reversibility**: 回滚方式
```

### Proposal 质量要求

Steward（守门人）从 5 个维度评分（每项 0-2 分，满分 10）：

| 维度 | 2 分 | 1 分 | 0 分 |
|------|------|------|------|
| 可行性 | 目标模块/接口存在 | 部分存在需新建 | 核心依赖不存在 |
| 可执行性 | 有具体文件名、函数名、接口设计 | 有方向但缺细节 | 只有目标没有路径 |
| 能力匹配 | 近期有成功记录 | 无历史记录 | 近期连续失败 |
| 历史风险 | 无相关失败 | 有失败但已修复 | 相同失败刚发生过 |
| 范围合理性 | 范围清晰独立 | 范围较大可分解 | 范围模糊或矛盾 |

评分规则：
- **>= 8 分**：ACCEPT，直接进入 pipeline
- **5-7 分**：PUSHBACK，附改进建议
- **<= 4 分**：REJECT

**注意**：修改 pipeline/agent/orchestrator 自身代码的 proposal，范围合理性上限为 1 分。这类变更应由人工完成。

### 生命周期

```
proposal.md 创建
      ↓
Proposal Gate ─── Steward 评分，ACCEPT/PUSHBACK/REJECT
      ↓
CLARIFY ─── 需求澄清，生成 clarify.md
      ↓
ENRICH ─── 生成 specs/*.md（行为规格 + 测试场景）
      ↓
Design Gate ─── Judge 评审 spec 质量，FAIL 则 ENRICH 重试（最多 2 次）
      ↓
IMPLEMENT ─── 按 specs 实现代码
      ↓
REVIEW ─── Reviewer 审查代码质量
      ↓
VERIFY ─── L1 pytest 验证 + LLM 三维验证（Completeness/Correctness/Coherence）
      ↓
OPTIMIZE ─── 代码优化
      ↓
REFLECT ─── 自我评估
      ↓
DELIVER ─── feature branch → deploy branch merge → push → tag
      ↓
归档到 archive/，daemon 自动重启加载新代码
```

## 监控与状态查看

### HTTP API

daemon 启动后提供以下端点（端口由 `--port` 参数决定）：

| 端点 | 说明 |
|------|------|
| `GET /api/pipeline-status` | **实时 pipeline 状态** — 当前 proposal、每 phase 进度/耗时/token |
| `GET /api/status.json` | Daemon 状态 — PID、cycle 数、当前 proposal、队列 |
| `GET /api/health` | 健康检查 — daemon 存活 + DB 可读性 |
| `GET /api/proposal-stats` | 历史统计 — 总量/成功率/平均耗时/最近 5 条 |

#### /api/pipeline-status 详解

最核心的监控端点，返回实时 phase-by-phase 进度：

```bash
curl -s http://localhost:58175/api/pipeline-status | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"daemon: {d['daemon']['state']} uptime={d['daemon']['uptime_seconds']:.0f}s\")
print(f\"active: {d['active_proposal']} @ {d['current_phase']}\")
for p in d['phase_progress']:
    s = {'PASS':'done','RUNNING':'>>>  ','PENDING':'wait ','FAIL':'FAIL '}[p['status']]
    dur = f\" {p.get('duration_s', p.get('elapsed_s', ''))}s\" if p.get('duration_s') or p.get('elapsed_s') else ''
    print(f\"  [{s}] {p['phase']}{dur}\")
for q in d['queue']:
    m = '*' if q['is_active'] else ' '
    print(f\"  {m} {q['name']}\")
"
```

输出示例：

```
daemon: running uptime=1847s
active: add-health-check @ implement
  [done] PROPOSAL_GATE
  [done] CLARIFY         92.6s
  [done] ENRICH          164.2s
  [done] DESIGN_GATE
  [>>>>] IMPLEMENT        45.1s
  [wait ] REVIEW
  [wait ] VERIFY
  [wait ] OPTIMIZE
  [wait ] REFLECT
  [wait ] DELIVER
  * add-health-check
    cleanup-stale-tests
```

#### /api/health

```bash
curl http://localhost:58175/api/health
# {"status": "healthy", "db_records": 138, "timestamp": "2026-05-25T08:24:04Z"}
# HTTP 200 = healthy, HTTP 503 = unhealthy
```

#### /api/proposal-stats

```bash
curl http://localhost:58175/api/proposal-stats
# {"total": 138, "by_outcome": {"success": 126, "skipped": 4, "reverted": 7},
#  "avg_duration_seconds": 469.9, "recent": [...]}
```

### Dashboard

浏览器打开：

```
http://<host>:58175/dashboard.html
```

自动刷新的 HTML 仪表盘，显示 Level 里程碑、成功率、Phase 耗时分布、提案队列。

### 日志

```bash
# systemd 方式
journalctl -u zsiga-daemon -f                    # 实时跟踪
journalctl -u zsiga-daemon --since "10 min ago"  # 最近 10 分钟
journalctl -u zsiga-daemon | grep "Phase\|Gate\|DONE\|FAIL"  # 关键事件

# 脚本方式
python -m zsiga daemon --port=58175  # 日志直接输出 stdout
```

#### 日志关键标记

| 标记 | 含义 |
|------|------|
| `--- xxx (project) ---` | 开始处理 proposal |
| `Proposal Gate: ACCEPT/REJECT` | Steward 判定 |
| `Phase 0/6: CLARIFY` | 进入 CLARIFY |
| `Phase 1/6: ENRICH` | 进入 ENRICH |
| `Design Gate PASS/FAIL` | Judge 判定 |
| `Judge feedback: ...` | Judge 反馈内容 |
| `Phase 2/6: IMPLEMENT` | 开始写代码 |
| `Verdict: PASS` | 验证通过 |
| `DONE: xxx` | 全部完成 |
| `Cycle complete: N changes processed` | 本轮结束 |

### Langfuse 可观测性

配置 `LANGFUSE_*` 环境变量后，每次 pipeline 运行会上报 trace 到 Langfuse：

- Trace 级别：`proposal:<change-name>`
- Phase 级别：`phase:clarify`、`phase:implement` 等
- Sub-agent 级别：`sub_agent:judge`、`sub_agent:scout` 等

访问 Langfuse dashboard 查看 LLM 调用链、token 消耗、耗时分析。

## 工作原理

```
openspec/changes/add-xxx/proposal.md   ← 你写这个
                ↓
        ┌─────────────────────────────────────────────────┐
        │  zsiga pipeline                                 │
        │                                                 │
        │  Proposal Gate → Steward 评分                   │
        │  CLARIFY     → 需求澄清                         │
        │  ENRICH      → specs + test scenarios           │
        │  Design Gate → Judge 评审 spec 质量              │
        │  IMPLEMENT   → 代码 + 测试 + commit             │
        │  REVIEW      → 代码审查                          │
        │  VERIFY      → pytest + LLM 三维验证             │
        │  OPTIMIZE    → 代码优化                          │
        │  REFLECT     → 自我评估                          │
        │  DELIVER     → feature branch → deploy → merge   │
        └─────────────────────────────────────────────────┘
                ↓
openspec/changes/archive/2026-05-25-add-xxx/  ← 完成后归档
```

## 安全机制

| 机制 | 说明 |
|------|------|
| Proposal Gate | Steward 5 维度评分，低分 proposal 自动拒绝 |
| Design Gate | Judge 评审 spec 质量，FAIL 则 ENRICH 重试 |
| Feature Branch 隔离 | IMPLEMENT 在独立分支，不碰 deploy branch |
| Auto Revert | 验证失败且修复超限时 git reset --hard 回滚 |
| Protected Paths | 不修改 migrations、生产配置、.env |
| DELIVER 原子性 | tag push / merge / deploy push 各自独立 try，互不阻塞 |

## 记忆系统

zsiga 从每次运行中积累经验到 `memory/learnings.jsonl`，自动注入到后续 agent 的 system prompt，避免重复犯错。

```bash
# 查看经验数量
wc -l memory/learnings.jsonl

# 手动添加经验
python3 -c "
from zsiga.memory.learn import record_lesson
record_lesson(
    title='target project uses venv/',
    context='stockshark has venv/bin/python',
    takeaway='detect venv/ first, use venv/bin/python -m pytest',
    pattern_key='tools.venv_detection',
    source='manual',
)
"
```

## 项目结构

```
zsiga/
├── zsiga.yaml                  # 全局配置
├── .zsiga.env                  # 环境变量（gitignore）
├── requirements.txt
├── zsiga/
│   ├── __main__.py             # 入口
│   ├── config.py               # 配置加载
│   ├── daemon.py               # Daemon 模式 + HTTP API
│   ├── git_ops.py              # Git 操作
│   ├── agent/
│   │   ├── loop.py             # LLM Agent Loop
│   │   ├── tools.py            # 工具注册
│   │   ├── roles.py            # 角色定义 + system prompt
│   │   ├── intent_router.py    # 意图路由
│   │   ├── sub_agent.py        # 子代理调度
│   │   └── langfuse_shim.py    # Langfuse 可观测性
│   ├── intake/
│   │   └── scanner.py          # Proposal 扫描
│   ├── memory/
│   │   ├── learn.py            # 经验记录
│   │   ├── journal.py          # 成长日记
│   │   └── context.py          # 上下文合成
│   ├── metrics/
│   │   ├── collector.py        # 指标采集
│   │   └── dashboard.py        # HTML 仪表盘
│   └── pipeline/
│       ├── orchestrator.py     # Pipeline 编排
│       ├── enricher.py         # ENRICH 阶段
│       ├── implementer.py      # IMPLEMENT 阶段
│       ├── verifier.py         # VERIFY 阶段
│       ├── proposal_gate.py    # Steward Gate
│       └── utils.py            # 工具函数 + 归档
├── openspec/
│   └── changes/                # Proposal 目录
│       ├── my-feature/
│       │   └── proposal.md
│       └── archive/            # 已完成归档
├── memory/
│   ├── active_context.md       # 注入到 agent 的上下文
│   ├── learnings.jsonl         # 经验库
│   └── journal.jsonl           # 成长日记
├── data/
│   ├── zsiga.db                # Pipeline 记录 DB
│   └── lock.pid                # PID 锁文件
└── skills/                     # Agent 行为约束
    ├── enrich.md
    ├── implement.md
    ├── verify.md
    └── safety.md
```

## License

MIT
