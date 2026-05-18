"""Post-implementation code review: dispatch review-role sub-agent and parse verdict."""

import re

from ..agent.loop import AgentLoop
from ..agent.sub_agent import SubAgentResult, create_with_role, run_sub_agent
from ..pipeline.implementer import _read_all_specs
from ..pipeline.utils import read_file
from ..transport import Transport, LocalTransport
from .. import git_ops

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
