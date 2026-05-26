"""Proposal Gate — Steward pre-flight review before pipeline entry.

Runs deterministic fact extraction first (zero LLM), then scout + analyst
agents in parallel to gather qualitative context, then dispatches a Steward
agent to evaluate the proposal.  Outputs ACCEPT / PUSHBACK / REJECT.
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
from .proposal_fact_extractor import extract_facts

log = logging.getLogger(__name__)


class GateVerdict(str, Enum):
    ACCEPT = "ACCEPT"
    PUSHBACK = "PUSHBACK"
    REJECT = "REJECT"


@dataclass
class ProposalGateResult:
    verdict: GateVerdict
    review_text: str
    score: int = 0
    scout_results: list[SubAgentResult] = None
    analyst_result: SubAgentResult = None
    elapsed_seconds: float = 0.0


def _parse_verdict(text: str) -> tuple[GateVerdict, int]:
    verdict = GateVerdict.ACCEPT
    score = 12

    vm = re.search(r"##\s*Verdict:\s*(ACCEPT|PUSHBACK|REJECT)", text, re.IGNORECASE)
    if vm:
        try:
            verdict = GateVerdict(vm.group(1).upper())
        except ValueError:
            pass

    sm = re.search(r"总分:\s*(\d+)\s*/\s*(?:10|12)", text)
    if sm:
        score = int(sm.group(1))

    return verdict, score


def _build_history_section(
    proposal_text: str,
    learning_weight_days: int = 90,
) -> str:
    lines = [l.strip() for l in proposal_text.splitlines() if l.strip()]
    title = lines[0] if lines else ""
    keywords = [w for w in re.split(r"[\s\-_:,.!?/\\]+", title) if len(w) >= 2][:8]

    if not keywords:
        return ""

    results = search_learnings(keywords)
    if not results:
        return ""

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
    api_key: str = "",
    model: str = "",
    base_url: str = None,
    proxy: str = None,
    score_accept: int = 10,
    score_pushback: int = 6,
    steward_max_turns: int = 3,
    steward_timeout: int = 90,
    learning_weight_days: int = 90,
    max_concurrency: int = 3,
) -> ProposalGateResult:
    import time
    transport = transport or LocalTransport()
    start = time.monotonic()

    proposal = read_file(f"{change_dir}/proposal.md", transport) or ""

    # --- Phase 0: deterministic fact extraction (zero LLM calls) ---
    fact_report = extract_facts(proposal, target_path)
    hard_facts = fact_report.to_prompt_section()
    if hard_facts:
        print(f"  🛡️ Deterministic facts: {fact_report.files_exist_summary}, {fact_report.symbols_exist_summary}")

    title = proposal.splitlines()[0] if proposal else "unknown"
    kw = title[:40]

    # --- Phase A: parallel qualitative context (scout × 2 + analyst × 1) ---
    scout1_instr = (
        f"以下文件和符号已经过确定性验证：\n{hard_facts}\n\n"
        f"基于以上事实，分析与「{kw}」相关的代码上下文：\n"
        "1) 读取已确认存在的文件，分析其结构和职责\n"
        "2) 确认 proposal 提到的符号是否与实际代码匹配\n"
        "3) 如果 proposal 描述与代码实际不符，指出具体差异\n"
        "不要重复验证文件是否存在 — 这已经确定了。"
    )

    scout2_instr = (
        f"搜索与「{kw}」相关的测试文件、配置文件和依赖关系。\n"
        f"确定性事实参考：\n{hard_facts}\n\n"
        "1) 这些文件是否有测试覆盖\n"
        "2) 是否涉及配置变更\n"
        "3) 外部依赖是否受影响\n"
        "排除 venv/ 和 .git/ 目录。"
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
                f"分析 proposal「{kw}」如果实施，会影响哪些模块和文件。\n"
                f"确定性事实：\n{hard_facts}\n\n"
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

    scout_results = [discovery_results[0], discovery_results[1]]
    analyst_result = discovery_results[2] if len(discovery_results) > 2 else None

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

{hard_facts}

**注意：以上「确定性事实」由代码验证产生，不可质疑。你的判断必须基于这些事实，而非 Scout 的推断。**

## Scout 定性分析（可参考但需独立判断）
{scout_facts}

## Analyst 影响分析（可参考但需独立判断）
{analyst_facts}

{history_section}

请基于以上信息，对 proposal 做出你的判断。确定性事实中的文件/符号存在性是绝对可靠的，
Scout 的分析可能包含推断或幻觉——如果 Scout 的结论与确定性事实矛盾，以确定性事实为准。"""

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

    if score >= score_accept:
        final_verdict = GateVerdict.ACCEPT
    elif score >= score_pushback:
        final_verdict = GateVerdict.PUSHBACK if parsed_verdict != GateVerdict.REJECT else GateVerdict.REJECT
    else:
        final_verdict = GateVerdict.REJECT

    elapsed = time.monotonic() - start
    print(
        f"  🛡️ Proposal Gate: verdict={final_verdict.value} score={score}/10 "
        f"({elapsed:.1f}s)"
    )

    review_path = f"{change_dir}/steward-review.md"
    escaped = review_text.replace("'", "'\\''")
    transport.run_shell(
        f"cat > '{review_path}' << 'ZSIGA_STEWARD_EOF'\n{review_text}\nZSIGA_STEWARD_EOF",
        timeout=10,
    )
    from datetime import datetime as _dt
    ts_path = f"{change_dir}/steward-review-{_dt.now().strftime('%Y%m%d-%H%M%S')}.md"
    transport.run_shell(
        f"cat > '{ts_path}' << 'ZSIGA_STEWARD_EOF'\n{review_text}\nZSIGA_STEWARD_EOF",
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
    from ..agent.tools import register_tools
    register_tools(agent, target_path, transport=transport)
