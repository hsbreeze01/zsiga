"""Proposal Gate — Steward pre-flight review before pipeline entry.

Runs scout + analyst agents in parallel to gather facts, then dispatches
a Steward agent to evaluate the proposal against historical experience
and codebase reality.  Outputs ACCEPT / PUSHBACK / REJECT.
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..agent.sub_agent import (
    create_with_role,
    run_sub_agent,
    dispatch_multi_role,
    collect_multi_role,
    MultiRoleHandle,
    SubAgentResult,
)
from ..transport import Transport, LocalTransport
from .utils import read_file
from ..memory.learn import search_learnings

log = logging.getLogger(__name__)


class GateVerdict(str, Enum):
    ACCEPT = "ACCEPT"
    PUSHBACK = "PUSHBACK"
    REJECT = "REJECT"


@dataclass
class ProposalGateResult:
    verdict: GateVerdict
    review_text: str        # Full steward output
    score: int = 0          # 0-8 total score
    scout_results: list[SubAgentResult] = None
    analyst_result: SubAgentResult = None
    elapsed_seconds: float = 0.0


def _parse_verdict(text: str) -> tuple[GateVerdict, int]:
    """Parse verdict and score from Steward output."""
    verdict = GateVerdict.ACCEPT
    score = 8

    # Extract verdict
    vm = re.search(r"##\s*Verdict:\s*(ACCEPT|PUSHBACK|REJECT)", text, re.IGNORECASE)
    if vm:
        try:
            verdict = GateVerdict(vm.group(1).upper())
        except ValueError:
            pass

    # Extract total score
    sm = re.search(r"总分:\s*(\d)\s*/\s*8", text)
    if sm:
        score = int(sm.group(1))

    return verdict, score


def _build_history_section(
    proposal_text: str,
    learning_weight_days: int = 90,
) -> str:
    """Search learnings.jsonl for similar failures and format them."""
    # Extract keywords from proposal title/first line
    lines = [l.strip() for l in proposal_text.splitlines() if l.strip()]
    title = lines[0] if lines else ""
    keywords = [w for w in re.split(r"[\s\-_:,.!?/\\]+", title) if len(w) >= 2][:8]

    if not keywords:
        return ""

    results = search_learnings(keywords)
    if not results:
        return ""

    # Filter to failures only, limit to 5
    failures = [r for r in results if r.get("type") == "lesson" and "FAIL" in r.get("title", "").upper()]
    failures = failures[:5]

    if not failures:
        return ""

    lines_out = ["## 历史教训（来自 learnings.jsonl）", ""]
    for f in failures:
        title = f.get("title", "unknown")
        ts = f.get("ts", "unknown date")[:10]
        takeaway = f.get("takeaway", "")[:120]
        pattern = f.get("pattern_key", "")
        lines_out.append(f"- **{title}** ({ts})")
        if takeaway:
            lines_out.append(f"  教训: {takeaway}")
        if pattern:
            lines_out.append(f"  模式: {pattern}")

    return "\n".join(lines_out)


async def run_proposal_gate(
    change_dir: str,
    target_path: str,
    transport: Transport = None,
    # LLM config
    api_key: str = "",
    model: str = "",
    base_url: str = None,
    proxy: str = None,
    # Gate config
    score_accept: int = 6,
    score_pushback: int = 3,
    steward_max_turns: int = 3,
    steward_timeout: int = 90,
    learning_weight_days: int = 90,
    max_concurrency: int = 3,
) -> ProposalGateResult:
    """Run the Proposal Gate: scout + analyst → steward → verdict.

    Returns a ProposalGateResult with the verdict and steward review text.
    """
    import time
    transport = transport or LocalTransport()
    start = time.monotonic()

    proposal = read_file(f"{change_dir}/proposal.md", transport) or ""

    # --- Phase A: parallel fact-gathering (scout × 2 + analyst × 1) ---
    title = proposal.splitlines()[0] if proposal else "unknown"
    kw = title[:40]

    # Extract specific file paths from proposal for targeted search
    import re as _re
    mentioned_files = _re.findall(r'[\w/]+\.py', proposal)
    files_hint = ", ".join(mentioned_files[:5]) if mentioned_files else ""

    scout1_instr = (
        f"验证以下文件是否存在于项目中: {files_hint}. " if files_hint else ""
    ) + (
        f"搜索项目中与「{kw}」直接相关的代码模块和函数。"
        "第一步：用 bash 运行 find . -not -path '*/venv/*' -not -path '*/.git/*' -name '*.py' 确认目录结构。"
        "第二步：用 read_file 读取关键文件头部（前30行）确认函数存在。"
        "排除 venv/ 和 .git/ 目录。"
        "告诉我：1) 每个文件是否存在及完整路径 2) 关键函数是否存在 3) 不存在时最近匹配。"
    )

    scout2_instr = (
        f"搜索项目中与「{kw}」相关的测试和配置。"
        "用 bash find 排除 venv/ 和 .git/ 搜索整个项目目录树。"
        "告诉我：1) 测试覆盖情况 2) 配置模式 3) 外部依赖。"
    )

    discovery_tasks = [
        {
            "role": "scout",
            "instruction": scout1_instr,
            "max_turns": 5,
            "timeout": 90,
        },
        {
            "role": "scout",
            "instruction": scout2_instr,
            "max_turns": 5,
            "timeout": 90,
        },
        {
            "role": "analyst",
            "instruction": (
                f"分析 proposal「{kw}」如果实施，会影响哪些模块和文件。"
                "输出：1) 受影响的模块列表 2) 需要修改的文件清单 3) 风险评估。"
            ),
            "max_turns": 5,
            "timeout": 90,
        },
    ]

    handle = dispatch_multi_role(
        tasks=discovery_tasks,
        api_key=api_key,
        model=model,
        base_url=base_url,
        proxy=proxy,
        target_path=target_path,
        transport=transport,
        max_concurrency=max_concurrency,
    )
    discovery_results = await collect_multi_role(handle)

    # Separate scout vs analyst results
    scout_results = [discovery_results[0], discovery_results[1]]
    analyst_result = discovery_results[2] if len(discovery_results) > 2 else None

    # Build fact sections
    scout_facts = ""
    for i, r in enumerate(scout_results):
        if r and r.success:
            scout_facts += f"\n### Scout #{i + 1} 结果\n{r.content}\n"
        else:
            scout_facts += f"\n### Scout #{i + 1} 失败\n"

    analyst_facts = ""
    if analyst_result and analyst_result.success:
        analyst_facts = f"\n### Analyst 影响分析\n{analyst_result.content}\n"

    # --- Phase B: build history section ---
    history_section = _build_history_section(proposal, learning_weight_days)

    # --- Phase C: Steward evaluation ---
    steward_agent = create_with_role("steward", api_key, model, base_url, proxy)
    register_tools_for_steward(steward_agent, target_path, transport)

    user_prompt = f"""## proposal.md
{proposal}

## Scout 事实信号（代码库中是否存在 proposal 提到的模块）
{scout_facts}

## Analyst 影响分析（改动会影响哪些文件/模块）
{analyst_facts}

{history_section}

请基于以上信息，对 proposal 做出你的判断。"""

    steward_result = await run_sub_agent(
        steward_agent,
        target_path,
        transport,
        user_prompt,
        max_turns=steward_max_turns,
        timeout_seconds=steward_timeout,
    )

    review_text = steward_result.content if steward_result.success else f"Steward failed: {steward_result.content}"

    # --- Phase D: parse verdict ---
    parsed_verdict, score = _parse_verdict(review_text)

    # Apply threshold override from config
    if score >= score_accept:
        final_verdict = GateVerdict.ACCEPT
    elif score >= score_pushback:
        final_verdict = GateVerdict.PUSHBACK if parsed_verdict != GateVerdict.REJECT else GateVerdict.REJECT
    else:
        final_verdict = GateVerdict.REJECT

    elapsed = time.monotonic() - start
    print(
        f"  🛡️ Proposal Gate: verdict={final_verdict.value} score={score}/8 "
        f"({elapsed:.1f}s)"
    )

    # Write steward-review.md to change_dir
    review_path = f"{change_dir}/steward-review.md"
    escaped = review_text.replace("'", "'\\''")
    transport.run_shell(
        f"cat > '{review_path}' << 'ZSIGA_STEWARD_EOF'\n{review_text}\nZSIGA_STEWARD_EOF",
        timeout=10,
    )

    return ProposalGateResult(
        verdict=final_verdict,
        review_text=review_text,
        score=score,
        scout_results=scout_results,
        analyst_result=analyst_result,
        elapsed_seconds=elapsed,
    )


def register_tools_for_steward(agent, target_path: str, transport: Transport):
    """Register read-only tools for steward agent."""
    from ..agent.tools import register_tools
    register_tools(agent, target_path, transport=transport)
