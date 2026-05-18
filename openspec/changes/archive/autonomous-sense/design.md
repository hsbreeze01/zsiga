# Design: L6 Autonomous Sense

## 架构决策

### AD-1: Sense 层在 Pipeline 之外，不在 Pipeline 之内

**决策**：Sense 作为 `run_cycle()` 的前置阶段，不修改现有 4-phase pipeline。

**理由**：pipeline 的 ENRICH→IMPLEMENT→VERIFY→DELIVER 已经验证可靠（84.9% 成功率）。Sense 层的职责是"发现问题"而非"解决问题"——问题一旦变成 proposal，就走现有 pipeline。这种分离让 sense 层的故障不影响 pipeline 稳定性。

### AD-2: 信号检测不用 LLM，只有 Proposer 用 LLM

**决策**：Sensor 和 Judge 纯规则驱动（bash/grep/python 逻辑），只有 Proposer 调用 LLM 生成 proposal 文本。

**理由**：信号检测频率高（每小时一次）、延迟要求低，LLM 调用成本高且不稳定。规则驱动保证 sense 层本身不会成为故障点。

### AD-3: 感知历史持久化到文件，不做数据库

**决策**：`memory/sense_history.jsonl` 追加写入，类似 learnings.jsonl。

**理由**：去重查询只需要"最近 24h 的信号"，jsonl 文件 + tail 足够。引入数据库增加复杂度，对 sense 层的价值不大。

### AD-4: 信号源可配置、可禁用

**决策**：每个信号源通过 zsiga.yaml 的 sense.signals 段独立启用/禁用。

**理由**：不同部署环境信号源不同（本地开发没有 journalctl、远程服务器没有 AIDesign 文档）。灵活配置避免硬编码。

## 数据流

```
zsiga.yaml (sense config)
       ↓
  run_cycle()
       ↓
  ┌─────────────────────────────────┐
  │  sensor.scan(targets, transports)│
  │  → list[Signal]                 │
  └──────────┬──────────────────────┘
             ↓
  ┌─────────────────────────────────┐
  │  judge.judge(signals, history)  │
  │  → list[JudgeResult]            │
  │  (去重 + 优先级 + 过滤)          │
  └──────────┬──────────────────────┘
             ↓
  ┌─────────────────────────────────┐
  │  proposer.propose(agent, judged)│
  │  → LLM 生成 proposal.md        │
  │  → 写入 openspec/changes/<slug> │
  └──────────┬──────────────────────┘
             ↓
  ┌─────────────────────────────────┐
  │  history.record(judged)         │
  │  → sense_history.jsonl          │
  └─────────────────────────────────┘
             ↓
  (现有 pipeline 处理所有 proposal)
```

## 新增文件

| 文件 | 职责 |
|------|------|
| `zsiga/intake/sensor.py` | 多信号源感知引擎，返回 `list[Signal]` |
| `zsiga/intake/proposer.py` | LLM 生成 proposal.md 并写入目标项目 |
| `zsiga/agent/judge.py` | 价值判断、去重、优先级排序 |
| `zsiga/memory/sense_history.jsonl` | 感知历史记录 |

## 修改文件

| 文件 | 修改内容 |
|------|---------|
| `zsiga/pipeline/orchestrator.py` | `run_cycle()` 开头增加 sense 阶段 |
| `zsiga/config.py` | 新增 `SenseConfig`、`SignalConfig` |
| `zsiga.yaml` | 新增 `sense:` 配置段 |
| `zsiga/metrics/types.py` | L6 milestone 定义 |

## 关键类型定义

```python
# sensor.py
@dataclass
class Signal:
    type: str           # health_check | git_changes | log_errors | quality | patterns
    project: str        # 目标项目名
    severity: str       # critical | high | medium | low
    data: dict          # 信号具体数据（URL、错误信息、diff 等）
    detected_at: str    # ISO timestamp

# judge.py
class SignalPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    NOISE = 4

@dataclass
class JudgeResult:
    signal: Signal
    priority: SignalPriority
    confidence: float
    reasoning: str
    estimated_effort: str
    affected_projects: list

# proposer.py — 无新类型，直接用 AgentLoop 生成 proposal 文本
```

## 配置模型

```yaml
sense:
  enabled: true
  interval_minutes: 60
  max_proposals_per_cycle: 3
  signals:
    health_check:
      enabled: true
      endpoints:
        - project: compass
          url: http://localhost:8087/health
        - project: factory
          url: http://localhost:8088/
    git_changes:
      enabled: true
      since: last_scan
    log_errors:
      enabled: true
      services: [d8q-compass, d8q-factory]
      since: 1h
    quality:
      enabled: true
      lint: true
      test: false
    patterns:
      enabled: true
      recurrence_threshold: 3
  filters:
    dedup_window_hours: 24
    min_priority: MEDIUM
```

## 安全考虑

- Sense 层本身是只读的（不修改任何目标项目文件）
- 只有 Proposer 写 proposal.md 到 openspec/changes/
- Proposer 生成的 proposal 走完整 pipeline（含 approval gate、dry_run、protected_paths）
- misfire_grace_time 类似问题：Sense 层的信号检测有超时保护，不会阻塞 pipeline
