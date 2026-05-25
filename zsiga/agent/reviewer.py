"""Post-implementation code review: dispatch review-role sub-agent and parse verdict."""

import logging
import os
import re
import time
from dataclasses import dataclass, field

from ..agent.loop import AgentLoop, RunResult
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
    llm_calls: int = 0
    tool_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0



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
    # Fallback: if diff is empty (proposal re-run on existing branch),
    # get the full branch diff from the first commit on the feature branch.
    if not diff.strip():
        try:
            mb_r = transport.run_shell(
                "git log --oneline --ancestry-path --reverse HEAD | head -1",
                cwd=target_path,
            )
            first_line = mb_r.get("stdout", "").strip()
            if first_line:
                first_sha = first_line.split()[0]
                diff = git_ops.diff(target_path, first_sha, transport=transport)
                print(
                    f"[REVIEW] diff was empty, using branch-first-commit "
                    f"{first_sha[:8]}: {len(diff)} chars"
                )
        except Exception:
            pass

    review_md_path = f"{change_dir}/review.md"

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
3. 你必须使用 write_file 工具将审查结果写入 {review_md_path}

关键规则：
- write_file 的 content 参数只能包含 review.md 的正文内容
- 不要把 tool_call、tool_response 或对话历史写入文件
- 不要用 bash cd 切换目录，项目根目录就是工作目录
- 所有信息已在 prompt 中提供，不需要运行 bash 查找项目文件
- 直接调用 write_file，不要先输出内容再调用

review.md 格式（content 参数必须严格遵循）：
Verdict: CLEAN 或 ISSUES_FOUND

Issues:（仅在 Verdict 为 ISSUES_FOUND 时列出）
1. [CRITICAL] 描述 + 代码证据
2. [SUGGESTION] 描述 + 代码证据
"""

    try:
        from .llm_router import LLMProfile, get_llm_profile
        HAS_ROUTER = True
    except ImportError:
        HAS_ROUTER = False
    base_url_default = getattr(agent.client, "base_url", None)
    if base_url_default is not None and not isinstance(base_url_default, str):
        base_url_default = str(base_url_default).rstrip("/")

    if HAS_ROUTER:
        profile = get_llm_profile(
            "review",
            LLMProfile(
                provider=getattr(agent, "provider", "zhipuai"),
                api_key=agent.client.api_key,
                model=agent.model,
                base_url=base_url_default,
            ),
        )
        print(
            f"[REVIEW] sub-agent provider={profile.provider} model={profile.model}",
            flush=True,
        )
        review_agent = create_with_role(
            "review",
            api_key=profile.api_key,
            model=profile.model,
            base_url=profile.base_url,
            proxy=None,
            provider=profile.provider,
        )
    else:
        print("[REVIEW] llm_router unavailable, using default client", flush=True)
        review_agent = create_with_role(
            "review",
            api_key=agent.client.api_key,
            model=agent.model,
            base_url=base_url_default,
            proxy=None,
        )

    print(
        f"[REVIEW] run_review: calling run_sub_agent "
        f"timeout={timeout_seconds}s max_turns={max_turns}",
        flush=True,
    )
    result = await run_sub_agent(
        review_agent,
        target_path,
        transport,
        user_prompt,
        max_turns=max_turns,
        timeout_seconds=timeout_seconds,
    )

    # Defensive fallback: if sub-agent did not write review.md, write it ourselves.
    # Also fix: if review.md contains tool_call artifacts, extract clean content.
    review_path = os.path.join(change_dir, 'review.md')
    logger = logging.getLogger(__name__)

    # Helper: extract clean verdict + issues from raw text (handles tool_call XML artifacts)
    def _extract_clean_review(raw: str) -> str:
        m = re.search(r'Verdict:\s*(CLEAN|ISSUES_FOUND)', raw)
        if not m:
            return raw
        verdict = m.group(1)
        clean = 'Verdict: ' + verdict + '\n'
        if verdict == 'ISSUES_FOUND':
            issues = re.findall(
                r'(\d+\.\s*\[(CRITICAL|SUGGESTION)\].+?)(?=\n\d+\. |$)',
                raw, re.DOTALL,
            )
            if issues:
                clean += '\nIssues:\n'
                for issue_text, _ in issues:
                    clean += issue_text + '\n'
        return clean

    if not os.path.isfile(review_path):
        logger.warning(
            'Review sub-agent did not call write_file; writing review.md from result.content'
        )
        os.makedirs(os.path.dirname(review_path), exist_ok=True)
        clean_content = _extract_clean_review(result.content)
        with open(review_path, 'w', encoding='utf-8') as f:
            f.write(clean_content)
    else:
        with open(review_path, 'r', encoding='utf-8') as f:
            written = f.read()
        # Detect tool_call artifacts (multiple formats: <tool_call:...>, <tool_calling>, etc.)
        if ('<tool_call' in written[:300] or written.strip().startswith('<tool_call')):
            logger.warning('review.md contains tool_call artifacts, extracting clean content')
            clean = _extract_clean_review(written)
            if clean != written:
                with open(review_path, 'w', encoding='utf-8') as f:
                    f.write(clean)
                logger.info('Cleaned review.md from tool_call artifacts')
            else:
                logger.warning('Could not extract verdict from tool_call artifacts')

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
    total_llm_calls = 0
    total_tool_calls = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    print(
        f"[REVIEW] ENTER run_review_loop change_dir={change_dir} "
        f"max_rounds={max_rounds} review_timeout={review_timeout}",
        flush=True,
    )

    for round_num in range(1, max_rounds + 1):
        print(f"[REVIEW] round {round_num}/{max_rounds} start", flush=True)
        # --- run review sub-agent ---
        sub_result = await run_review(
            agent, change_dir, target_path, pre_impl_sha, transport,
            max_turns=review_max_turns, timeout_seconds=review_timeout,
        )
        # Accumulate sub-agent metrics
        total_llm_calls += getattr(sub_result, "llm_calls", 0)
        total_tool_calls += getattr(sub_result, "tool_calls", 0)
        total_prompt_tokens += getattr(sub_result, "prompt_tokens", 0)
        total_completion_tokens += getattr(sub_result, "completion_tokens", 0)

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
                llm_calls=total_llm_calls,
                tool_calls=total_tool_calls,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
            )

        if verdict == "UNKNOWN":
            return ReviewLoopResult(
                final_verdict="UNKNOWN",
                rounds_executed=round_num,
                fix_attempts=fix_attempts,
                elapsed_seconds=time.monotonic() - t_start,
                last_issues=[],
                had_critical=had_critical,
                llm_calls=total_llm_calls,
                tool_calls=total_tool_calls,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
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
                llm_calls=total_llm_calls,
                tool_calls=total_tool_calls,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
            )

        had_critical = True

        # Attempt fix for CRITICAL issues
        changed_files = _get_changed_files(target_path, pre_impl_sha, transport)
        system_prompt, user_prompt = _build_fix_prompt(
            issues, changed_files, target_path,
        )
        fix_result = await agent.run(system_prompt, user_prompt, max_turns=fix_max_turns, timeout_seconds=300)
        # Accumulate fix RunResult metrics
        if isinstance(fix_result, RunResult):
            total_llm_calls += fix_result.llm_calls
            total_tool_calls += fix_result.tool_calls
            total_prompt_tokens += fix_result.prompt_tokens
            total_completion_tokens += fix_result.completion_tokens
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
        llm_calls=total_llm_calls,
        tool_calls=total_tool_calls,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
    )
