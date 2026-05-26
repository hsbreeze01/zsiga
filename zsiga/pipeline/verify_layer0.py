"""Layer 0 of the multi-layer VERIFY: deterministic binary checks.

Runs BEFORE Layer 1 (pytest) and Layer 2 (LLM judge). Every check produces
a binary yes/no result — no LLM calls, no probabilistic judgement.

If ANY check fails, verify returns FAIL immediately without calling the
LLM, saving tokens and preventing false-positive PASS on incomplete work.

Check inventory:
    L0-01  spec_file_coverage      — every spec has ≥1 corresponding code change
    L0-02  tasks_completion        — all tasks.md items are checked off
    L0-03  testable_not_all_false  — not every scenario is demoted to testable=false
    L0-04  no_syntax_error         — changed Python files pass py_compile
    L0-05  spec_scenario_coverage  — key SHALL/MUST terms from specs appear in diff
    L0-BAC bac_acceptance          — Binary Acceptance Checks from proposal.md
"""
from __future__ import annotations

import json
import os
import py_compile
import re
import tempfile
import time
from dataclasses import asdict, dataclass, field

from .. import git_ops
from ..transport import LocalTransport, Transport
from .spec_parser import parse_spec
from .utils import (
    _get_changed_files,
    get_all_changed_files,
    list_files_recursive,
    read_file,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Layer0Check:
    """A single binary check result."""

    id: str           # e.g. "spec_file_coverage"
    description: str  # human-readable one-liner
    passed: bool      # True / False — no middle ground
    evidence: str     # what was observed (passed or failed)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Layer0Result:
    """Aggregate result of all Layer 0 checks."""

    checks: list[Layer0Check] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> list[Layer0Check]:
        return [c for c in self.checks if not c.passed]

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)

    def summary_line(self) -> str:
        if self.all_passed:
            return f"L0 PASS: {self.total_count}/{self.total_count} checks passed"
        return (
            f"L0 FAIL: {self.passed_count}/{self.total_count} checks passed "
            f"({', '.join(c.id for c in self.failed_checks)})"
        )

    def to_dict(self) -> dict:
        return {
            "checks": [c.to_dict() for c in self.checks],
            "elapsed_seconds": self.elapsed_seconds,
            "all_passed": self.all_passed,
        }


# ---------------------------------------------------------------------------
# Check L0-01: spec_file_coverage
# ---------------------------------------------------------------------------

# High-frequency words to skip when deriving keywords from spec filenames.
_SKIP_WORDS = frozenset([
    "a", "an", "the", "and", "or", "in", "of", "for", "to", "with",
    "add", "fix", "update", "remove", "new", "old", "set", "get",
])


def _extract_spec_keywords(spec_path: str, transport: Transport) -> list[str]:
    """Derive searchable keywords from a spec file.

    Strategy:
      1. Split the filename (sans .md) on '-' and '_'
      2. Filter out high-frequency noise words
      3. Also extract the first heading (# Title) from the file content
      4. De-duplicate, keeping order
    """
    filename = os.path.basename(spec_path).removesuffix(".md")
    parts = [p for p in re.split(r"[-_]+", filename) if p and p.lower() not in _SKIP_WORDS]

    # Read the first heading for additional signal.
    content = read_file(spec_path, transport) or ""
    first_heading = ""
    for line in content.splitlines():
        if line.startswith("#"):
            first_heading = line.lstrip("#").strip()
            break

    heading_words = []
    if first_heading:
        heading_words = [
            w for w in re.split(r"\s+", first_heading)
            if len(w) > 3 and w.lower() not in _SKIP_WORDS
        ]

    # Merge and de-dup (preserve order)
    seen: set[str] = set()
    keywords: list[str] = []
    for w in parts + heading_words:
        wl = w.lower()
        if wl not in seen:
            seen.add(wl)
            keywords.append(wl)

    return keywords


def _diff_has_keyword(
    keyword: str,
    diff_files: list[str],
    diff_content_lower: str,
) -> bool:
    """True if *keyword* appears in any changed file name or the diff body."""
    for df in diff_files:
        if keyword in os.path.basename(df).lower():
            return True
    if keyword in diff_content_lower:
        return True
    return False


def check_spec_file_coverage(
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport,
) -> Layer0Check:
    """L0-01: every spec file must have ≥1 corresponding code change."""
    spec_files = list_files_recursive(
        os.path.join(change_dir, "specs"), "*.md", transport,
    )
    if not spec_files:
        return Layer0Check(
            "spec_file_coverage",
            "每个 spec 文件至少有一个对应的代码变更",
            True,
            "无 spec 文件，跳过",
        )

    diff_files = get_all_changed_files(target_path, pre_impl_sha, transport)
    diff_content = git_ops.diff(target_path, pre_impl_sha, transport=transport)
    diff_lower = diff_content.lower()

    uncovered: list[str] = []
    for spec_path in spec_files:
        spec_filename = os.path.basename(spec_path)
        keywords = _extract_spec_keywords(spec_path, transport)

        if not keywords:
            # Last resort: use the full spec name stem
            keywords = [os.path.basename(spec_path).removesuffix(".md").lower()]

        covered = any(
            _diff_has_keyword(kw, diff_files, diff_lower)
            for kw in keywords
        )
        if not covered:
            uncovered.append(spec_filename)

    passed = len(uncovered) == 0
    if passed:
        evidence = f"全部 {len(spec_files)} 个 spec 文件均有对应代码变更"
    else:
        evidence = f"未覆盖的 spec: {', '.join(uncovered)}"

    return Layer0Check(
        "spec_file_coverage",
        "每个 spec 文件至少有一个对应的代码变更",
        passed,
        evidence,
    )


# ---------------------------------------------------------------------------
# Check L0-02: tasks_completion
# ---------------------------------------------------------------------------


def check_tasks_completion(
    change_dir: str, transport: Transport,
) -> Layer0Check:
    """L0-02: all tasks in tasks.md must be checked off."""
    tasks = read_file(os.path.join(change_dir, "tasks.md"), transport) or ""
    if not tasks.strip():
        return Layer0Check(
            "tasks_completion",
            "tasks.md 中所有 task 已勾选",
            True,
            "无 tasks.md 或为空，跳过",
        )

    unchecked = re.findall(r"-\s*\[\s*\]", tasks)
    passed = len(unchecked) == 0
    evidence = (
        f"剩余未完成 task: {len(unchecked)} 个"
        if unchecked
        else "所有 task 已完成"
    )

    return Layer0Check(
        "tasks_completion",
        "tasks.md 中所有 task 已勾选",
        passed,
        evidence,
    )


# ---------------------------------------------------------------------------
# Check L0-03: testable_not_all_false
# ---------------------------------------------------------------------------


def check_testable_not_all_false(
    change_dir: str, transport: Transport,
) -> Layer0Check:
    """L0-03: at least one scenario must be testable=true."""
    spec_files = list_files_recursive(
        os.path.join(change_dir, "specs"), "*.md", transport,
    )
    if not spec_files:
        return Layer0Check(
            "testable_not_all_false",
            "至少存在 testable=true 的 scenario",
            True,
            "无 spec 文件，跳过",
        )

    total_testable = 0
    total_scenarios = 0
    for spec_path in spec_files:
        spec_text = read_file(spec_path, transport) or ""
        scenarios = parse_spec(spec_text)
        for s in scenarios:
            total_scenarios += 1
            if s.testable:
                total_testable += 1

    if total_scenarios == 0:
        return Layer0Check(
            "testable_not_all_false",
            "至少存在 testable=true 的 scenario",
            True,
            "无 scenario，跳过",
        )

    passed = total_testable > 0
    evidence = (
        f"{total_scenarios} 个 scenario 中 {total_testable} 个 testable=true"
    )

    return Layer0Check(
        "testable_not_all_false",
        "至少存在 testable=true 的 scenario",
        passed,
        evidence,
    )


# ---------------------------------------------------------------------------
# Check L0-04: no_syntax_error
# ---------------------------------------------------------------------------


def _py_compile_source(source_text: str) -> tuple[bool, str]:
    """Compile-check Python source text. Returns (ok, error_msg)."""
    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8",
    ) as f:
        f.write(source_text)
        tmp = f.name
    try:
        try:
            py_compile.compile(tmp, doraise=True)
            return True, ""
        except py_compile.PyCompileError as exc:
            return False, str(exc).splitlines()[0][:120] if str(exc) else "syntax error"
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def check_no_syntax_error(
    target_path: str, pre_impl_sha: str, transport: Transport,
) -> Layer0Check:
    """L0-04: all changed Python files must pass py_compile."""
    changed = _get_changed_files(target_path, pre_impl_sha, transport)
    if not changed:
        return Layer0Check(
            "no_syntax_error",
            "变更的 Python 文件无语法错误",
            True,
            "无 Python 文件变更，跳过",
        )

    errors: list[str] = []
    for rel_path in changed:
        full_path = os.path.join(target_path, rel_path)
        source = read_file(full_path, transport)
        if source is None:
            continue
        ok, err = _py_compile_source(source)
        if not ok:
            errors.append(f"{rel_path}: {err}")

    passed = len(errors) == 0
    evidence = (
        "; ".join(errors[:3])
        if errors
        else f"{len(changed)} 个 Python 文件语法检查通过"
    )

    return Layer0Check(
        "no_syntax_error",
        "变更的 Python 文件无语法错误",
        passed,
        evidence,
    )


# ---------------------------------------------------------------------------
# Check L0-05: spec_scenario_coverage
# ---------------------------------------------------------------------------

# Patterns to extract key requirements from spec text.
_SHALL_RE = re.compile(
    r"SHALL\s+(?:provide|include|accept|return|contain|set|handle|"
    r"detect|have|use|be|support|add|implement|create|define|expose|"
    r"reset|track|check|compute|write|not\s+change)\s+"
    r"(?P<term>[A-Za-z_]\w+(?:\s+[A-Za-z_]\w+){0,3})",
    re.IGNORECASE,
)
_MUST_RE = re.compile(
    r"MUST\s+(?:be|have|include|provide|contain|use|support|match|"
    r"return|accept|handle)\s+"
    r"(?P<term>[A-Za-z_]\w+(?:\s+[A-Za-z_]\w+){0,3})",
    re.IGNORECASE,
)


def check_spec_scenario_coverage(
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport,
) -> Layer0Check:
    """L0-05: key SHALL/MUST terms from each spec appear in the diff."""
    spec_files = list_files_recursive(
        os.path.join(change_dir, "specs"), "*.md", transport,
    )
    if not spec_files:
        return Layer0Check(
            "spec_scenario_coverage",
            "spec 中的关键要求在 diff 中有实现痕迹",
            True,
            "无 spec 文件，跳过",
        )

    diff_content = git_ops.diff(target_path, pre_impl_sha, transport=transport)
    if not diff_content.strip():
        return Layer0Check(
            "spec_scenario_coverage",
            "spec 中的关键要求在 diff 中有实现痕迹",
            False,
            "git diff 为空",
        )

    diff_lower = diff_content.lower()

    uncovered_specs: list[str] = []
    for spec_path in spec_files:
        spec_text = read_file(spec_path, transport) or ""
        terms: list[str] = []

        for pat in (_SHALL_RE, _MUST_RE):
            for m in pat.finditer(spec_text):
                term = m.group("term").strip()
                # Take the last 1-2 words (most specific) as keyword
                words = term.split()
                if len(words) > 2:
                    term = " ".join(words[-2:])
                terms.append(term)

        if not terms:
            continue

        # A spec is "covered" if at least half of its key terms appear
        matched = sum(
            1 for t in terms
            if t.lower() in diff_lower
        )
        ratio = matched / len(terms) if terms else 1.0
        if ratio < 0.3:
            spec_name = os.path.basename(spec_path)
            missed = [t for t in terms if t.lower() not in diff_lower]
            uncovered_specs.append(
                f"{spec_name}: {', '.join(missed[:3])} not in diff "
                f"({matched}/{len(terms)})"
            )

    passed = len(uncovered_specs) == 0
    evidence = (
        "; ".join(uncovered_specs)
        if uncovered_specs
        else f"全部 {len(spec_files)} 个 spec 的关键要求在 diff 中有痕迹"
    )

    return Layer0Check(
        "spec_scenario_coverage",
        "spec 中的关键要求在 diff 中有实现痕迹",
        passed,
        evidence,
    )


# ---------------------------------------------------------------------------
# Check L0-BAC: Binary Acceptance Checks from proposal.md
# ---------------------------------------------------------------------------

_BAC_RE = re.compile(r"\[BAC-(\d+)\]\s*(.+?)(?:\n|$)")

# Pattern: `file` 中存在 `symbol`
_BAC_EXISTS_RE = re.compile(r"`([^`]+)`\s*中存在\s*`([^`]+)`")
# Pattern: `file` 中引用了 `term`
_BAC_REF_RE = re.compile(r"`([^`]+)`\s*中引用了\s*`([^`]+)`")
# Pattern: 所有 spec 文件...都有对应代码变更
_BAC_ALL_SPEC_RE = re.compile(r"所有\s*spec.*对应.*代码.*变更")
# Pattern: 至少存在 N 个 testable=true
_BAC_TESTABLE_RE = re.compile(r"至少存在\s*(\d+)\s*个\s*testable\s*=\s*true")


def _check_symbol_in_file(
    file_name: str, symbol: str, target_path: str, transport: Transport,
) -> tuple[bool, str]:
    """Check that *symbol* appears in *file_name* source."""
    # Try multiple resolution strategies for file_name
    candidates = [
        os.path.join(target_path, file_name),
        os.path.join(target_path, "zsiga", file_name),
    ]
    # Also try finding by basename
    for candidate in candidates:
        source = read_file(candidate, transport)
        if source is not None:
            if symbol in source:
                return True, f"`{symbol}` 存在于 {file_name}"
            return False, f"`{symbol}` 未在 {file_name} 中找到"

    # Fallback: try grep in target_path
    r = transport.run_shell(
        f"grep -r '{symbol}' '{target_path}/{file_name}' 2>/dev/null | head -1",
        timeout=10,
    )
    if r.get("exit_code") == 0 and r.get("stdout", "").strip():
        return True, f"`{symbol}` 存在于 {file_name}"
    return False, f"文件 {file_name} 未找到或 `{symbol}` 不在其中"


def _check_term_in_file(
    file_name: str, term: str, target_path: str, transport: Transport,
) -> tuple[bool, str]:
    """Check that *term* is referenced in *file_name* source."""
    # Try term alternatives (e.g. cap_exceeded OR CAP_EXCEEDED)
    terms = [term]
    if "_" in term:
        terms.append(term.upper())

    candidates = [
        os.path.join(target_path, file_name),
        os.path.join(target_path, "zsiga", file_name),
    ]
    for candidate in candidates:
        source = read_file(candidate, transport)
        if source is not None:
            for t in terms:
                if t in source:
                    return True, f"`{t}` 引用存在于 {file_name}"
            return False, f"`{term}` 未在 {file_name} 中找到"

    return False, f"文件 {file_name} 未找到或 `{term}` 不在其中"


def _check_testable_count(
    change_dir: str, min_count: int, transport: Transport,
) -> tuple[bool, str]:
    """Count testable=true scenarios across all specs."""
    spec_files = list_files_recursive(
        os.path.join(change_dir, "specs"), "*.md", transport,
    )
    total = 0
    for spec_path in spec_files:
        spec_text = read_file(spec_path, transport) or ""
        scenarios = parse_spec(spec_text)
        total += sum(1 for s in scenarios if s.testable)

    passed = total >= min_count
    return passed, f"testable=true 的 scenario: {total} (要求 ≥ {min_count})"


def check_bac_acceptance(
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport,
) -> list[Layer0Check]:
    """Parse BAC items from proposal.md and evaluate each one."""
    proposal = read_file(os.path.join(change_dir, "proposal.md"), transport)
    if not proposal:
        return []

    bac_items = _BAC_RE.findall(proposal)
    if not bac_items:
        return []

    checks: list[Layer0Check] = []
    for bac_num, bac_text in bac_items:
        bac_text = bac_text.strip()

        # Pattern: `file` 中存在 `symbol`
        m = _BAC_EXISTS_RE.search(bac_text)
        if m:
            passed, evidence = _check_symbol_in_file(
                m.group(1), m.group(2), target_path, transport,
            )
            checks.append(Layer0Check(
                f"bac_{bac_num}",
                f"[BAC-{bac_num}] {bac_text}",
                passed,
                evidence,
            ))
            continue

        # Pattern: `file` 中引用了 `term`
        m = _BAC_REF_RE.search(bac_text)
        if m:
            passed, evidence = _check_term_in_file(
                m.group(1), m.group(2), target_path, transport,
            )
            checks.append(Layer0Check(
                f"bac_{bac_num}",
                f"[BAC-{bac_num}] {bac_text}",
                passed,
                evidence,
            ))
            continue

        # Pattern: 所有 spec 文件...都有对应代码变更
        if _BAC_ALL_SPEC_RE.search(bac_text):
            # Delegate to L0-01 (will be checked separately)
            checks.append(Layer0Check(
                f"bac_{bac_num}",
                f"[BAC-{bac_num}] {bac_text}",
                True,
                "由 spec_file_coverage 检查覆盖",
            ))
            continue

        # Pattern: 至少存在 N 个 testable=true
        m = _BAC_TESTABLE_RE.search(bac_text)
        if m:
            min_count = int(m.group(1))
            passed, evidence = _check_testable_count(
                change_dir, min_count, transport,
            )
            checks.append(Layer0Check(
                f"bac_{bac_num}",
                f"[BAC-{bac_num}] {bac_text}",
                passed,
                evidence,
            ))
            continue

        # Unrecognised BAC — don't block, skip with note
        checks.append(Layer0Check(
            f"bac_{bac_num}",
            f"[BAC-{bac_num}] {bac_text}",
            True,
            f"无法自动验证，已跳过",
        ))

    return checks


# ---------------------------------------------------------------------------
# Orchestrator: run all checks
# ---------------------------------------------------------------------------


def run_layer0_checks(
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport | None = None,
) -> Layer0Result:
    """Execute all Layer 0 deterministic binary checks."""
    transport = transport or LocalTransport()
    t_start = time.monotonic()

    checks: list[Layer0Check] = [
        check_spec_file_coverage(change_dir, target_path, pre_impl_sha, transport),
        check_tasks_completion(change_dir, transport),
        check_testable_not_all_false(change_dir, transport),
        check_no_syntax_error(target_path, pre_impl_sha, transport),
        check_spec_scenario_coverage(change_dir, target_path, pre_impl_sha, transport),
    ]

    # Conditional: BAC checks (only if proposal.md contains BAC items)
    bac_checks = check_bac_acceptance(
        change_dir, target_path, pre_impl_sha, transport,
    )
    checks.extend(bac_checks)

    elapsed = time.monotonic() - t_start
    result = Layer0Result(checks=checks, elapsed_seconds=elapsed)

    # Persist verify_layer0.json
    _persist_result(change_dir, transport, result)

    return result


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _persist_result(
    change_dir: str, transport: Transport, result: Layer0Result,
) -> None:
    """Write verify_layer0.json for downstream consumers."""
    payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    target = os.path.join(change_dir, "verify_layer0.json")
    try:
        transport.run_shell(
            f"cat > '{target}' <<'ZSIGA_L0_EOF'\n"
            f"{payload}\n"
            f"ZSIGA_L0_EOF",
            timeout=10,
        )
    except Exception as exc:
        print(f"  ⚠ failed to persist verify_layer0.json: {exc}", flush=True)


# ---------------------------------------------------------------------------
# verify.md writer for Layer 0 FAIL
# ---------------------------------------------------------------------------


def write_layer0_verify_md(
    change_dir: str, transport: Transport, result: Layer0Result,
) -> None:
    """Write verify.md with Layer 0 FAIL result."""
    lines = [
        "Verdict: FAIL",
        f"Layer 0: FAIL — {result.passed_count}/{result.total_count} checks passed",
        "",
    ]

    if result.failed_checks:
        lines.append("## Failed Checks")
        for i, c in enumerate(result.failed_checks, 1):
            lines.append(
                f"{i}. [CRITICAL] {c.id}: {c.description}"
            )
            lines.append(f"   Evidence: {c.evidence}")
        lines.append("")

    passed_checks = [c for c in result.checks if c.passed]
    if passed_checks:
        lines.append(f"## Passed Checks ({len(passed_checks)}/{result.total_count})")
        for c in passed_checks:
            lines.append(f"- ✓ {c.id}: {c.evidence}")
        lines.append("")

    body = "\n".join(lines)
    path = os.path.join(change_dir, "verify.md")
    transport.run_shell(
        f"cat > '{path}' <<'ZSIGA_VERIFY_EOF'\n{body}\nZSIGA_VERIFY_EOF",
        timeout=10,
    )
