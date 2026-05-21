import re

from ..agent.loop import AgentLoop
from ..transport import LocalTransport, Transport
from .. import git_ops
from .utils import read_file
from .verify_layer1 import (
    Layer1Result,
    has_non_testable_scenarios,
    run_layer1_pytest,
)


VERIFIER_SYSTEM = """你是 zsiga 的验证引擎。你的任务是对比 specs 和实际代码改动，判断实现质量，并将结果写入 verify.md。

关键规则：
1. 所有信息（specs、diff、Layer 1 pytest 结果、测试/lint 结果）已在 prompt 中提供，你不需要读取任何文件
2. 不要使用 read_file、bash、search 等工具来读取代码
3. 直接使用 write_file 工具写入 verify.md — 这是你在本次任务中唯一需要调用的工具
4. 基于已提供的信息做出判断，不要尝试获取额外信息

## Layer 1 / Layer 2 分工（重要）

zsiga 的 verify 分两层：
- **Layer 1**: 对每个 testable=true 的 scenario 自动跑 pytest（机械验证），结果在下方 prompt 中给出
- **Layer 2**: 你（LLM）只判断那些 testable=false 的 scenario，以及完整性 / 一致性等机械测不出的部分

**Layer 1 结果是 authoritative**：
- 如果 Layer 1 verdict=FAIL，你的最终 Verdict **必须**是 FAIL，无论你认为 Layer 2 多么完美
- 如果 Layer 1 verdict=PASS 或 vacuous（无 testable scenario），按你对剩余 scenario 的判断给出 Verdict

verify.md 格式（严格遵守）：
Verdict: PASS 或 FAIL
Layer 1: {PASS|FAIL|vacuous} — {summary line}
Completeness: ✓/✗ 一句话（仅针对 Layer 2 范围）
Correctness: ✓/✗ 一句话
Coherence: ✓/✗ 一句话
Issues: (如果有)
  1. [CRITICAL/WARNING] 描述"""


def _format_layer1_section(layer1: Layer1Result) -> str:
    """Render the Layer 1 block injected into the Layer 2 LLM prompt."""
    if layer1.vacuous:
        warn = f" (warning: {layer1.warning})" if layer1.warning else ""
        return (
            "## Layer 1 (pytest, mechanical) — vacuous\n"
            f"- 无 testable scenario 或无 test 文件{warn}\n"
            "- 你需要完整地评估所有 scenario\n"
        )
    verdict = "PASS" if layer1.passed else "FAIL"
    output_tail = layer1.pytest_output[-1500:] if layer1.pytest_output else "(empty)"
    extra = ""
    if not layer1.passed:
        extra = (
            "\n!!! Layer 1 FAIL: 你的最终 Verdict 必须是 FAIL。\n"
            "Issues 列表中至少加一条 [CRITICAL] 引用具体的 pytest 失败。\n"
        )
    return (
        f"## Layer 1 (pytest, mechanical) — {verdict}\n"
        f"- 跑了 {layer1.scenarios_tested} 个 testable scenarios，"
        f"{len(layer1.test_files)} 个测试文件\n"
        f"- pytest exit code: {layer1.pytest_exit_code}\n"
        f"- 测试文件: {', '.join(layer1.test_files) if layer1.test_files else '(none)'}\n"
        f"\n```\n{output_tail}\n```\n"
        f"{extra}"
    )


def _enforce_l1_verdict(change_dir: str, transport: Transport, layer1: Layer1Result) -> None:
    """Defensive: if L1 FAILed but verify.md says PASS, override to FAIL.

    This guards against an LLM that ignored the prompt instruction. We
    rewrite only the ``Verdict:`` line and prepend a Layer 1 OVERRIDE
    block so the original LLM judgement remains visible for review.
    """
    if layer1.vacuous or layer1.passed:
        return
    path = f"{change_dir}/verify.md"
    content = read_file(path, transport) or ""
    if not content:
        return
    if "Verdict: FAIL" in content:
        return  # already correct
    # Replace the first ``Verdict: ...`` line with FAIL, prepend override note
    new_content = re.sub(
        r"^Verdict:\s*[A-Za-z_]+",
        "Verdict: FAIL",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    override_block = (
        "<!-- L1 OVERRIDE: pytest failed; LLM original verdict overridden to FAIL -->\n"
        f"<!-- exit_code={layer1.pytest_exit_code}, "
        f"scenarios={layer1.scenarios_tested} -->\n"
    )
    new_content = override_block + new_content
    transport.run_shell(
        f"cat > '{path}' <<'ZSIGA_VERIFY_EOF'\n{new_content}\nZSIGA_VERIFY_EOF",
        timeout=10,
    )


async def verify(agent: AgentLoop, change_dir: str, target_path: str,
                 pre_impl_sha: str,
                 transport: Transport = None,
                 mech_results: dict = None,
                 venv_python: str = None,
                 **kwargs):
    """Two-layer verify: pytest first, LLM judge with L1 context, enforce L1 verdict."""
    from .implementer import _read_all_specs

    transport = transport or LocalTransport()

    # ---- Layer 1: mechanical pytest ----
    layer1 = run_layer1_pytest(
        change_dir, target_path, transport=transport, venv_python=venv_python,
    )
    print(f"  verify {layer1.summary_line()}", flush=True)

    # Decide whether Layer 2 LLM judge is needed
    needs_layer2 = layer1.vacuous or has_non_testable_scenarios(change_dir, transport)

    if not needs_layer2:
        # Pure-L1 fast path: write verify.md ourselves, skip the LLM call.
        _write_pure_layer1_verify_md(change_dir, transport, layer1)
        return None

    # ---- Layer 2: LLM judge ----
    specs = _read_all_specs(change_dir, transport)
    design = read_file(f"{change_dir}/design.md", transport) or ""
    tasks = read_file(f"{change_dir}/tasks.md", transport) or ""
    diff = git_ops.diff(target_path, pre_impl_sha, transport=transport)

    mech_section = ""
    if mech_results:
        test_status = "✅ PASSED" if mech_results["test"]["passed"] else "❌ FAILED"
        lint_status = "✅ PASSED" if mech_results["lint"]["passed"] else "❌ FAILED"
        mech_section = f"""
## 预跑测试结果（不要重复运行）
- Tests: {test_status}
  ```
  {mech_results['test']['output'][-1500:]}
  ```
- Lint: {lint_status}
  ```
  {mech_results['lint']['output'][-1500:]}
  ```
"""

    layer1_section = _format_layer1_section(layer1)

    user_prompt = f"""## Change: {change_dir}

{layer1_section}

### specs:
{specs}

### design.md:
{design}

### tasks.md:
{tasks}

### 实际改动 (git diff):
{diff[:15000]}
{mech_section}
基于以上信息判断实现质量（注意：testable=true 的 scenario 已由 Layer 1 判定，你不需要重新对它们下结论；你的核心任务是审查 testable=false 的 scenario + 完整性/一致性）。
将结果写入 {change_dir}/verify.md。不要运行测试或 lint。"""

    result = await agent.run(VERIFIER_SYSTEM, user_prompt, **kwargs)

    # Defensive: if L1 failed and LLM somehow wrote PASS, override.
    _enforce_l1_verdict(change_dir, transport, layer1)

    return result


def _write_pure_layer1_verify_md(
    change_dir: str, transport: Transport, layer1: Layer1Result,
) -> None:
    """Compose verify.md when no Layer 2 judgement is required."""
    verdict = "PASS" if layer1.passed else "FAIL"
    files_md = ", ".join(layer1.test_files) if layer1.test_files else "(none)"
    output_tail = layer1.pytest_output[-2000:] if layer1.pytest_output else "(empty)"
    body = (
        f"Verdict: {verdict}\n"
        f"Layer 1: {verdict} — {layer1.summary_line()}\n"
        f"Completeness: ✓ all scenarios are testable, mechanical run carried verdict\n"
        f"Correctness: ✓ pytest exit code = {layer1.pytest_exit_code}\n"
        f"Coherence: ✓ no Layer 2 LLM judgement required\n"
        f"\n## Layer 1 detail\n"
        f"- scenarios tested: {layer1.scenarios_tested}\n"
        f"- test files: {files_md}\n"
        f"- pytest exit code: {layer1.pytest_exit_code}\n"
        f"\n```\n{output_tail}\n```\n"
    )
    transport.run_shell(
        f"cat > '{change_dir}/verify.md' <<'ZSIGA_VERIFY_EOF'\n"
        f"{body}\n"
        f"ZSIGA_VERIFY_EOF",
        timeout=10,
    )


def read_verdict(change_dir: str, transport: Transport = None) -> str:
    content = read_file(f"{change_dir}/verify.md", transport)
    if content is None:
        return "UNKNOWN"
    match = re.search(r"Verdict:\s*(PASS|FAIL)", content)
    return match.group(1) if match else "UNKNOWN"
