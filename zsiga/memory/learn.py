import json
from datetime import datetime
from pathlib import Path

_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"


def record_lesson(title: str, context: str, takeaway: str,
                  pattern_key: str = None, source: str = "pipeline"):
    lesson = {
        "type": "lesson",
        "ts": datetime.now().isoformat(),
        "source": source,
        "title": title,
        "context": context,
        "takeaway": takeaway,
    }
    if pattern_key:
        lesson["pattern_key"] = pattern_key

    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    learnings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(learnings_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(lesson, ensure_ascii=False) + "\n")


def record_outcome(change_name: str, project: str, success: bool,
                   phase: str, detail: str = None):
    if success:
        return

    title = f"FAIL: {change_name} at {phase}"
    ctx = f"project={project}, phase={phase}"
    if detail:
        ctx += f", detail={detail[:300]}"

    error_type = _classify_error(detail or "")
    takeaway = _generate_takeaway(error_type, phase, detail)
    pattern_key = f"pipeline.fail.{phase}.{error_type}"
    record_lesson(title, ctx, takeaway, pattern_key, source="orchestrator")


def _classify_error(detail: str) -> str:
    if "E401" in detail:
        return "lint_e401_multi_import"
    if "E702" in detail:
        return "lint_e702_semicolon"
    if "E701" in detail:
        return "lint_e701_one_line"
    if "E722" in detail:
        return "lint_e722_bare_except"
    if "E501" in detail:
        return "lint_e501_line_length"
    if "FAILED" in detail or "test session" in detail.lower():
        return "test_failure"
    if "timeout" in detail.lower():
        return "timeout"
    return "unknown"


def _generate_takeaway(error_type: str, phase: str, detail: str) -> str:
    takeaways = {
        "lint_e401_multi_import": "Pre-split multi-import lines in implementation; ruff --fix can auto-fix this",
        "lint_e702_semicolon": "Never use semicolons to join statements; always use separate lines",
        "lint_e701_one_line": "Never put if/for body on same line as keyword; always use newline + indent",
        "lint_e722_bare_except": "Always use 'except Exception:' instead of bare 'except:'",
        "lint_e501_line_length": "Keep lines under 88 chars; break long strings or function signatures",
        "test_failure": "Check test output for specific assertion errors; verify test expectations match implementation API",
        "timeout": "Task exceeded time budget; consider reducing scope or splitting into smaller changes",
    }
    return takeaways.get(error_type, f"Failed at {phase}: review error and adjust approach")
