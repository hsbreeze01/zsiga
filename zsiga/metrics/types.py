from dataclasses import dataclass, field
from datetime import datetime
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
    "label": "L2: Better Tools",
    "criteria": [
        ("successful_changes", 10, "累计成功 change 数 >= 10"),
        ("success_rate_pct", 70, "总成功率 >= 70%"),
        ("distinct_projects", 3, "覆盖 >= 3 个不同目标项目"),
        ("lessons_learned", 20, "积累 >= 20 条经验教训"),
    ],
}

MILESTONE_L3 = {
    "label": "L3: Self-Evolution",
    "criteria": [
        ("successful_changes", 30, "累计成功 change 数 >= 30"),
        ("success_rate_pct", 85, "总成功率 >= 85%"),
        ("verify_pass_rate_pct", 80, "验证通过率 >= 80%"),
        ("lessons_learned", 50, "积累 >= 50 条经验教训"),
        ("first_pass_test_rate_pct", 60, "首次测试通过率 >= 60%"),
    ],
}
