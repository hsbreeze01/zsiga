from dataclasses import dataclass, field
from enum import Enum


class Phase(str, Enum):
    ENRICH = "enrich"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    DELIVER = "deliver"


class Outcome(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    TIMEOUT = "timeout"
    REVERTED = "reverted"
    SKIPPED = "skipped"


@dataclass
class PhaseRecord:
    phase: Phase
    outcome: Outcome
    turns_used: int = 0
    seconds_used: float = 0.0
    fix_attempts: int = 0
    llm_calls: int = 0
    tool_calls: int = 0
    detail: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    compaction_count: int = 0
    sub_agent_count: int = 0


@dataclass
class ChangeRecord:
    change_name: str
    project: str
    outcome: Outcome
    phases: list[PhaseRecord] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    lessons_count: int = 0

    def to_dict(self) -> dict:
        return {
            "change_name": self.change_name,
            "project": self.project,
            "outcome": self.outcome.value,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "lessons_count": self.lessons_count,
            "phases": [
                {
                    "phase": p.phase.value,
                    "outcome": p.outcome.value,
                    "turns_used": p.turns_used,
                    "seconds_used": round(p.seconds_used, 1),
                    "fix_attempts": p.fix_attempts,
                    "llm_calls": p.llm_calls,
                    "tool_calls": p.tool_calls,
                    "detail": p.detail,
                    "prompt_tokens": p.prompt_tokens,
                    "completion_tokens": p.completion_tokens,
                    "compaction_count": p.compaction_count,
                    "sub_agent_count": p.sub_agent_count,
                }
                for p in self.phases
            ],
        }


MILESTONE_L2 = {
    "label": "Level 2: Code Architect",
    "icon": "⚡",
    "color": "#f59e0b",
    "criteria": [
        ("successful_changes", 10, "累计成功 change 数 >= 10"),
        ("success_rate_pct", 70, "总成功率 >= 70%"),
        ("distinct_projects", 3, "覆盖 >= 3 个不同目标项目"),
        ("lessons_learned", 20, "积累 >= 20 条经验教训"),
    ],
}

MILESTONE_L3 = {
    "label": "Level 3: Self-Evolution",
    "icon": "🔧",
    "color": "#8b5cf6",
    "description": "zsiga 获得修改自身代码的能力，具备 LSP 级代码感知和专业子代理分化",
    "tasks": [
        {
            "id": "lsp_integration",
            "title": "LSP 集成",
            "description": "集成 pyright/pylsp，提供 goto_definition、find_references、diagnostics 工具",
            "deliverables": ["agent/lsp_tools.py", "tools: goto_def, find_refs, diagnostics"],
            "acceptance": "LSP 工具在 target project 上可用，goto_definition 能跳转到定义，diagnostics 能返回错误",
        },
        {
            "id": "self_modify_gate",
            "title": "Self-Modify 门控",
            "description": "允许 zsiga 修改 zsiga/ 自身代码，通过 scope 扩展 + 安全校验实现",
            "deliverables": ["pipeline/orchestrator.py", "pipeline/implementer.py", "config.py"],
            "acceptance": "zsiga 能读取并修改自身源码文件，同时保护 config.yaml 和 memory/ 不被误改",
        },
        {
            "id": "specialist_sub_agents",
            "title": "专业子代理分化",
            "description": "区分 explore(快速搜索)、implement(写代码)、review(验证) 三种子代理角色，各自有专门 system prompt",
            "deliverables": ["agent/roles.py", "agent/sub_agent.py"],
            "acceptance": "三种角色子代理可独立创建并执行，各有不同的 system prompt 和行为约束",
        },
        {
            "id": "pattern_mining",
            "title": "跨会话模式挖掘",
            "description": "从 learnings.jsonl 中提取 recurring patterns，自动识别重复失败模式并生成避坑建议",
            "deliverables": ["memory/pattern_miner.py", "memory/context.py"],
            "acceptance": "能从历史 learnings 中识别出现 ≥3 次的 pattern_key，自动注入到 active_context",
        },
        {
            "id": "l3_validation",
            "title": "L3 验证：修改自身 + LSP 导航",
            "description": "zsiga 使用 LSP 工具定位自身代码中的模式，并通过 self-modify 修复一个自身 bug",
            "deliverables": ["一个成功的 self-modify change 记录"],
            "acceptance": "zsiga 用 goto_definition 找到目标函数 → 修改 → 自测通过 → 记录为成功 change",
        },
    ],
    "criteria": [
        ("successful_changes", 30, "累计成功 change 数 >= 30"),
        ("success_rate_pct", 75, "总成功率 >= 75%"),
        ("l3_tasks_completed", 5, "L3 能力任务完成 >= 5"),
    ],
}

MILESTONE_L4 = {
    "label": "Level 4: Multi-Project Orchestrator",
    "icon": "🌐",
    "color": "#06b6d4",
    "description": "zsiga 从固定流水线升级为动态任务分解器，支持跨项目协调和意图路由",
    "tasks": [
        {
            "id": "intent_router",
            "title": "Intent Router",
            "description": "请求分类引擎：trivial(直接执行) / exploration(派发 explore) / implementation(走 pipeline) / ambiguous(询问用户)",
            "deliverables": ["agent/intent_router.py", "router: classify() → route()"],
            "acceptance": "给定任意用户消息，能正确分类意图并选择执行路径",
        },
        {
            "id": "task_decomposer",
            "title": "跨项目任务分解",
            "description": "将高层指令（如'给所有项目做回归测试'）分解为多项目子任务列表，支持并行派发和结果汇总",
            "deliverables": ["agent/task_decomposer.py", "orchestrator: decompose() → dispatch_parallel() → aggregate()"],
            "acceptance": "输入跨项目指令 → 自动分解为项目级子任务 → 并行执行 → 汇总报告",
        },
        {
            "id": "todo_orchestration",
            "title": "Todo 驱动编排",
            "description": "动态 todo list 作为协调机制，替代固定 4 阶段 pipeline；支持 in_progress/completed 状态追踪",
            "deliverables": ["agent/todo.py", "dashboard: todo progress card"],
            "acceptance": "todo list 可动态创建/更新/完成，每个 todo 有独立状态，dashboard 实时展示进度",
        },
        {
            "id": "escalation_protocol",
            "title": "升级路径 (Escalation)",
            "description": "3 次修复失败后自动升级：尝试不同策略 → 标记需要人类介入 → 生成诊断报告",
            "deliverables": ["agent/escalation.py", "orchestrator: escalate() with strategy rotation"],
            "acceptance": "修复循环 3 次失败后自动触发升级，生成诊断报告并暂停等待人工介入",
        },
        {
            "id": "cross_project_validation",
            "title": "L4 验证：跨项目回归测试",
            "description": "zsiga 接收'全量回归测试'指令 → 自动分解为 5 个项目子任务 → 并行执行 → 汇总测试报告",
            "deliverables": ["一次成功的跨项目回归测试记录"],
            "acceptance": "5 个项目的测试结果汇总在一份报告中，区分 pass/fail/unknown",
        },
    ],
    "criteria": [
        ("successful_changes", 50, "累计成功 change 数 >= 50"),
        ("success_rate_pct", 80, "总成功率 >= 80%"),
        ("l4_tasks_completed", 5, "L4 能力任务完成 >= 5"),
    ],
}

MILESTONE_L5 = {
    "label": "Level 5: Autonomous Engineer",
    "icon": "🚀",
    "color": "#22c55e",
    "description": "zsiga 具备完整自主工程能力：意图理解、专家委派、并行执行、自我审查、skill 演化",
    "tasks": [
        {
            "id": "phase0_intent_gate",
            "title": "Phase 0 Intent Gate",
            "description": "每条消息先分类再路由，支持 research/implementation/investigation/evaluation/fix/open-ended 六种意图",
            "deliverables": ["agent/intent_gate.py", "gate: verbalize → classify → route"],
            "acceptance": "给定任意用户输入，能 verbalize 意图、分类、并选择正确的执行路径",
        },
        {
            "id": "parallel_background",
            "title": "并行后台代理",
            "description": "同时发射 2-5 个 explore agent，异步收集结果后综合决策；支持后台发射+回调收集模式",
            "deliverables": ["agent/background_pool.py", "pool: dispatch_many() → collect_all()"],
            "acceptance": "同时派发 3 个搜索任务，全部完成后综合结果做出决策，比顺序执行快 2x+",
        },
        {
            "id": "skill_evolution",
            "title": "Skill 演化",
            "description": "从历史会话中自动发现 recurring patterns → 提炼为可复用的 skill markdown → 自动更新 skills/",
            "deliverables": ["skills/skill_evolver.py", "skills/_evolution_log.md"],
            "acceptance": "能从 learnings.jsonl 识别高频 pattern → 自动生成/更新 skill .md 文件",
        },
        {
            "id": "self_review",
            "title": "自我审查循环",
            "description": "完成实现后自动触发 review 子代理 → 发现问题 → 修复 → 再审，最多 2 轮",
            "deliverables": ["agent/reviewer.py", "pipeline: impl → review → fix → re-review"],
            "acceptance": "每次实现完成后自动触发 review，review 结果记录在 metrics 中",
        },
        {
            "id": "failure_recovery",
            "title": "失败恢复协议",
            "description": "3 次失败→回滚→分析根因→换策略→再试→不行则生成诊断报告给用户",
            "deliverables": ["agent/recovery.py", "recovery: rollback → diagnose → retry_with_strategy → report"],
            "acceptance": "失败后能自动回滚、生成根因分析、尝试不同策略（而非重复相同修复）",
        },
        {
            "id": "l5_validation",
            "title": "L5 验证：端到端自主任务",
            "description": "zsiga 接收一个模糊需求（如'优化 stockshark 性能'），自主完成意图分析→分解→探索→实现→审查→交付",
            "deliverables": ["一次端到端自主任务记录"],
            "acceptance": "从模糊需求到代码交付，全程无人工干预，成功 change 记录",
        },
    ],
    "criteria": [
        ("successful_changes", 80, "累计成功 change 数 >= 80"),
        ("success_rate_pct", 85, "总成功率 >= 85%"),
        ("l5_tasks_completed", 6, "L5 能力任务完成 >= 6"),
    ],
}

ALL_MILESTONES = [MILESTONE_L2, MILESTONE_L3, MILESTONE_L4, MILESTONE_L5]
