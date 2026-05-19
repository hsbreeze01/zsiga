"""Post-implementation code review: dispatch review-role sub-agent and parse verdict."""

import re
import time
from dataclasses import dataclass, field

from ..agent.loop import AgentLoop
from ..agent.sub_agent import SubAgentResult, create_with_role, run_sub_agent
from ..pipeline.implementer import _read_all_specs
from ..pipeline.utils import read_file, _get_changed_files
from ..transport import Transport, LocalTransport
from .. import git_ops


@dataclass
class ReviewLoopResult:
    """Result of the self-review loop."""

    final_verdict: str  # "CLEAN", "ISSUES_FOUND", "UNKNOWN"
    rounds_executed: int
    fix_attempts: int
    elapsed_seconds: float
    last_issues: list[dict] = field(default_factory=list)
    had_critical: bool = False

REVIEW_SYSTEM = """你是 zsiga 的代码审查引擎。你的职责是审查实现变更，判断是否满足规格要求。

规则：
- 只能使用只读工具（bash、read_file、search、list_files、ast_search、goto_definition、find_references、diagnostics）
- 逐条检查每条 spec 要求是否在代码 diff 中被覆盖
- 检查常见代码质量问题（死代码、缺失错误处理、命名）
- 输出 review.md 文件到指定目录

review.md 格式（严格遵守）：
```
Verdict: CLEAN 或 ISSUES_FOUND

Issues:（仅在 Verdict 为 ISSUES_FOUND 时列出）
1. [CRITICAL] 描述 + 代码证据
2. [SUGGESTION] 描述 + 代码证据
```

如果所有 spec 要求都被覆盖且无代码质量问题，Verdict 为 CLEAN。
如果发现任何问题，Verdict 为 ISSUES_FOUND，并按严重程度分类为 CRITICAL 或 SUGGESTION。
"""


async def run_review(
    agent: AgentLoop,
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport = None,
    max_turns: int = 10,
    timeout_seconds: int = 180,
) -> SubAgentResult:
    """Dispatch review-role sub-agent to analyze implementation against specs.

    The sub-agent writes review.md in change_dir.
    Returns the SubAgentResult from the sub-agent execution.
    """
    transport = transport or LocalTransport()

    specs = _read_all_specs(change_dir, transport)
    design = read_file(f"{change_dir}/design.md", transport) or ""
    tasks = read_file(f"{change_dir}/tasks.md", transport) or ""
    diff = git_ops.diff(target_path, pre_impl_sha, transport=transport)

    user_prompt = f"""## Change: {change_dir}

### specs:
{specs}

### design.md:
{design}

### tasks.md:
{tasks}

### 实际改动 (git diff):
{diff[:15000]}

基于以上信息：
1. 逐条检查每条 spec 要求是否在 diff 中被实现
2. 检查代码质量（死代码、错误处理、命名）
3. 将结果写入 {change_dir}/review.md

review.md 格式：
Verdict: CLEAN 或 ISSUES_FOUND

Issues:（仅在 Verdict 为 ISSUES_FOUND 时列出）
1. [CRITICAL] 描述 + 代码证据
2. [SUGGESTION] 描述 + 代码证据
"""

    review_agent = create_with_role(
        "review",
        api_key=agent.client.api_key,
        model=agent.model,
        base_url=getattr(agent.client, "base_url", None),
        proxy=None,
    )

    result = await run_sub_agent(
        review_agent,
        target_path,
        transport,
        user_prompt,
        max_turns=max_turns,
        timeout_seconds=timeout_seconds,
    )

    return result


def parse_review_verdict(
    change_dir: str, transport: Transport = None
) -> tuple[str, list[dict]]:
    """Parse review.md and return (verdict, issues).

    verdict: "CLEAN" or "ISSUES_FOUND" or "UNKNOWN"
    issues: [{"severity": "CRITICAL"|"SUGGESTION", "description": str}, ...]
    """
    content = read_file(f"{change_dir}/review.md", transport)
    if content is None:
        return "UNKNOWN", []

    verdict_match = re.search(r"Verdict:\s*(CLEAN|ISSUES_FOUND)", content)
    if not verdict_match:
        return "UNKNOWN", []

    verdict = verdict_match.group(1)

    if verdict == "CLEAN":
        return "CLEAN", []

    # Parse issues from ISSUES_FOUND verdict
    issues = []
    issue_pattern = re.compile(
        r"\d+\.\s*\[(CRITICAL|SUGGESTION)\]\s*(.+?)(?=\n\d+\.|$)",
        re.DOTALL,
    )
    for match in issue_pattern.finditer(content):
        severity = match.group(1)
        description = match.group(2).strip()
        if description:
            issues.append({
                "severity": severity,
                "description": description,
            })

    return verdict, issues


def _has_critical(issues: list[dict]) -> bool:
    """Return True if any issue has severity CRITICAL."""
    return any(i.get("severity") == "CRITICAL" for i in issues)


def _build_fix_prompt(issues: list[dict], changed_files: list[str],
                      target_path: str) -> tuple[str, str]:
    """Build system/user prompts for the review fix agent."""
    critical_desc = "\n".join(
        f"- [{i['severity']}] {i['description']}"
        for i in issues if i.get("severity") == "CRITICAL"
    )
    changed_info = (
        "\n本次变更的文件（只修这些）: "
        + (", ".join(changed_files) if changed_files else "无")
    )
    path_hint = f"\n项目根目录: {target_path}"

    system = (
        "你是 zsiga 的审查修复引擎。严格遵守以下规则：\n"
        "1. 只修改本次变更引入的文件（上方列出的）\n"
        "2. 绝对不要修改任何未列出的文件\n"
        "3. 不要添加新路由、新端点、新功能 — 只修复 CRITICAL 问题\n"
        "4. 只修报错的那一行，不要重排整个文件的 import 或做大规模重构\n"
        "5. 修复后运行 ruff check 确认无 lint 错误"
    )
    user = (
        f"审查发现的 CRITICAL 问题:\n{critical_desc}"
        f"{changed_info}{path_hint}\n\n"
        "只修改上方列出的文件来修复 CRITICAL 问题。"
    )
    return system, user


async def run_review_loop(
    agent: AgentLoop,
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport = None,
    max_rounds: int = 2,
    review_max_turns: int = 10,
    review_timeout: int = 180,
    fix_max_turns: int = 6,
) -> ReviewLoopResult:
    """Execute review loop: review -> fix -> re-review, up to *max_rounds*.

    SUGGESTION-only issues are treated as CLEAN (no fix triggered).
    Only CRITICAL issues trigger a fix attempt via ``agent.run()``.
    """
    transport = transport or LocalTransport()
    t_start = time.monotonic()
    fix_attempts = 0
    had_critical = False

    for round_num in range(1, max_rounds + 1):
        # --- run review sub-agent ---
        await run_review(
            agent, change_dir, target_path, pre_impl_sha, transport,
            max_turns=review_max_turns, timeout_seconds=review_timeout,
        )
        verdict, issues = parse_review_verdict(change_dir, transport)

        # CLEAN or unknown -> done
        if verdict == "CLEAN":
            return ReviewLoopResult(
                final_verdict="CLEAN",
                rounds_executed=round_num,
                fix_attempts=fix_attempts,
                elapsed_seconds=time.monotonic() - t_start,
                last_issues=[],
                had_critical=had_critical,
            )

        if verdict == "UNKNOWN":
            return ReviewLoopResult(
                final_verdict="UNKNOWN",
                rounds_executed=round_num,
                fix_attempts=fix_attempts,
                elapsed_seconds=time.monotonic() - t_start,
                last_issues=[],
                had_critical=had_critical,
            )

        # verdict == ISSUES_FOUND — check for CRITICAL
        if not _has_critical(issues):
            # SUGGESTION-only -> treat as pass
            return ReviewLoopResult(
                final_verdict="CLEAN",
                rounds_executed=round_num,
                fix_attempts=fix_attempts,
                elapsed_seconds=time.monotonic() - t_start,
                last_issues=issues,
                had_critical=had_critical,
            )

        had_critical = True

        # Attempt fix for CRITICAL issues
        changed_files = _get_changed_files(target_path, pre_impl_sha, transport)
        system_prompt, user_prompt = _build_fix_prompt(
            issues, changed_files, target_path,
        )
        await agent.run(system_prompt, user_prompt, max_turns=fix_max_turns)
        fix_attempts += 1

        # Loop continues to next round for re-review

    # Exhausted max_rounds
    return ReviewLoopResult(
        final_verdict="ISSUES_FOUND",
        rounds_executed=max_rounds,
        fix_attempts=fix_attempts,
        elapsed_seconds=time.monotonic() - t_start,
        last_issues=issues,
        had_critical=had_critical,
    )
