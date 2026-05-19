"""跨项目任务分解器 — 将高层指令分解为多项目子任务列表"""
import re
from dataclasses import dataclass, field


@dataclass
class SubTask:
    project: str
    description: str
    priority: int = 0
    depends_on: list[str] = field(default_factory=list)
    parallel_safe: bool = True


@dataclass
class Decomposition:
    original_instruction: str
    subtasks: list[SubTask]
    parallel_groups: list[list[str]]
    estimated_total: str


_PROJECT_PATTERNS = {
    "compass": re.compile(r"compass|stockcompass|策略|stock|股票|分析", re.IGNORECASE),
    "dataagent": re.compile(r"data.?agent|dataagent|资讯|新闻|news", re.IGNORECASE),
    "stockshark": re.compile(r"stockshark|shark|行情|实时|quote", re.IGNORECASE),
    "factory": re.compile(r"datafactory|factory|数据工厂|etl|pipeline", re.IGNORECASE),
    "infopublisher": re.compile(r"infopublisher|publisher|发布|推送|publish", re.IGNORECASE),
    "zsiga": re.compile(r"zsiga|自身|self|进化|evolv", re.IGNORECASE),
}

_ALL_PROJECTS = list(_PROJECT_PATTERNS.keys())


def decompose(instruction: str, available_projects: list[str] = None,
              originating_project: str = None) -> Decomposition:
    """将高层指令分解为项目级子任务列表。

    Parameters
    ----------
    instruction : str
        高层用户指令（如"给所有项目做回归测试"）
    available_projects : list[str], optional
        可用项目列表，默认全部
    originating_project : str, optional
        change 所属的原始项目。如果提供且 keyword 只匹配到 1 个其他项目，
        则视为 keyword 噪声，不触发跨项目分解。

    Returns
    -------
    Decomposition
        分解结果，含子任务列表和并行分组
    """
    projects = available_projects or _ALL_PROJECTS
    matched = _match_projects(instruction, projects)

    if not matched:
        matched = projects

    if originating_project:
        matched = [originating_project]

    generic_tasks = _detect_generic_tasks(instruction)

    subtasks = []
    for proj in matched:
        task_desc = generic_tasks or f"执行: {instruction}"
        subtasks.append(SubTask(
            project=proj,
            description=task_desc,
            priority=1 if generic_tasks else 0,
            parallel_safe=True,
        ))

    parallel_groups = _build_parallel_groups(subtasks)

    return Decomposition(
        original_instruction=instruction,
        subtasks=subtasks,
        parallel_groups=parallel_groups,
        estimated_total=f"{len(subtasks)} 个子任务，{len(parallel_groups)} 个并行组",
    )


def _match_projects(instruction: str, available: list[str]) -> list[str]:
    matched = []
    for proj in available:
        pattern = _PROJECT_PATTERNS.get(proj)
        if pattern and pattern.search(instruction):
            matched.append(proj)
    return matched


def _detect_generic_tasks(instruction: str) -> str:
    patterns = [
        (re.compile(r"回归测试|测试|test|regression", re.IGNORECASE), "运行测试套件"),
        (re.compile(r"lint|检查|check|代码质量", re.IGNORECASE), "运行代码质量检查"),
        (re.compile(r"部署|deploy|发布|release", re.IGNORECASE), "执行部署流程"),
        (re.compile(r"依赖|upgrade|更新|update", re.IGNORECASE), "更新依赖"),
    ]
    for pattern, task_desc in patterns:
        if pattern.search(instruction):
            return task_desc
    return ""


def _build_parallel_groups(subtasks: list[SubTask]) -> list[list[str]]:
    dep_free = [t for t in subtasks if not t.depends_on and t.parallel_safe]
    dep_bound = [t for t in subtasks if t.depends_on or not t.parallel_safe]

    groups = []
    if dep_free:
        groups.append([t.project for t in dep_free])
    for t in dep_bound:
        groups.append([t.project])

    return groups


def aggregate_results(results: dict[str, dict]) -> dict:
    """汇总多项目执行结果。

    Parameters
    ----------
    results : dict[str, dict]
        {project: {status: str, detail: str, ...}}

    Returns
    -------
    dict
        汇总报告 {total, passed, failed, unknown, details}
    """
    passed = sum(1 for r in results.values() if r.get("status") == "pass")
    failed = sum(1 for r in results.values() if r.get("status") == "fail")
    unknown = len(results) - passed - failed
    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "unknown": unknown,
        "details": results,
    }
