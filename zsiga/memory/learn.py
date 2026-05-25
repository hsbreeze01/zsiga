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

    try:
        from ..metrics.db import record_lesson as _db_record
        _db_record(
            text=takeaway or title,
            pattern_key=pattern_key or "",
            category=source,
            ts=lesson["ts"],
        )
    except Exception:
        pass


def record_outcome(change_name: str, project: str, success: bool,
                   phase: str, detail: str = None,
                   error_domain: str = None,
                   root_cause: str = None,
                   prevention: str = None):
    if success:
        return

    title = f"FAIL: {change_name} at {phase}"
    ctx = f"project={project}, phase={phase}"
    if detail:
        ctx += f", detail={detail[:300]}"

    # Auto-infer classification when not provided
    classification = _classify_failure(detail or "")
    if error_domain is None:
        error_domain = classification["error_domain"]
    if root_cause is None:
        root_cause = classification["root_cause_key"]
    if prevention is None:
        prevention = classification["prevention"]

    pattern_key = f"{error_domain}.{root_cause}"
    what_happened = title if not detail else f"{title}: {detail[:200]}"

    # Write structured lesson record
    lesson = {
        "type": "lesson",
        "ts": datetime.now().isoformat(),
        "source": "orchestrator",
        "title": title,
        "context": ctx,
        "takeaway": prevention,
        "pattern_key": pattern_key,
        "error_domain": error_domain,
        "root_cause": root_cause,
        "prevention": prevention,
        "what_happened": what_happened,
    }

    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    learnings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(learnings_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(lesson, ensure_ascii=False) + "\n")

    try:
        from ..metrics.db import record_lesson as _db_record
        _db_record(
            text=prevention or what_happened,
            pattern_key=pattern_key,
            category=error_domain,
            ts=lesson["ts"],
        )
    except Exception:
        pass


def _classify_failure(detail: str) -> dict:
    """Two-layer error classification: domain + root_cause_key.

    Returns dict with keys: error_domain, root_cause_key, prevention.
    """
    # Lint errors → code domain
    lint_rules = {
        "E401": {
            "root_cause_key": "lint.e401",
            "prevention": "Pre-split multi-import lines in implementation; ruff --fix can auto-fix this",
        },
        "E702": {
            "root_cause_key": "lint.e702",
            "prevention": "Never use semicolons to join statements; always use separate lines",
        },
        "E701": {
            "root_cause_key": "lint.e701",
            "prevention": "Never put if/for body on same line as keyword; always use newline + indent",
        },
        "E722": {
            "root_cause_key": "lint.e722",
            "prevention": "Always use 'except Exception:' instead of bare 'except:'",
        },
        "E501": {
            "root_cause_key": "lint.e501",
            "prevention": "Keep lines under 88 chars; break long strings or function signatures",
        },
        "E741": {
            "root_cause_key": "lint.e741",
            "prevention": "Avoid ambiguous variable names like 'l', 'O', 'I'; use descriptive names",
        },
    }
    for code, info in lint_rules.items():
        if code in detail:
            return {
                "error_domain": "code",
                "root_cause_key": info["root_cause_key"],
                "prevention": info["prevention"],
            }

    # Test failures → code domain with subcategories
    if "AssertionError" in detail or "assertion" in detail.lower():
        return {
            "error_domain": "code",
            "root_cause_key": "test.assertion",
            "prevention": "Check test output for specific assertion errors; verify test expectations match implementation API",
        }
    if "ImportError" in detail or "ModuleNotFoundError" in detail:
        return {
            "error_domain": "code",
            "root_cause_key": "test.import",
            "prevention": "Verify import paths and module structure; ensure __init__.py exists",
        }
    if "FAILED" in detail or "test session" in detail.lower():
        return {
            "error_domain": "code",
            "root_cause_key": "test.assertion",
            "prevention": "Check test output for specific assertion errors; verify test expectations match implementation API",
        }
    if "ssh" in detail.lower():
        return {
            "error_domain": "infrastructure",
            "root_cause_key": "ssh.timeout",
            "prevention": "Verify SSH connectivity and retry with backoff",
        }
    if "rate_limit" in detail.lower() or "429" in detail:
        return {
            "error_domain": "infrastructure",
            "root_cause_key": "api.rate_limit",
            "prevention": "Implement exponential backoff for API calls",
        }
    if "timeout" in detail.lower():
        return {
            "error_domain": "infrastructure",
            "root_cause_key": "timeout",
            "prevention": "Task exceeded time budget; consider reducing scope or splitting into smaller changes",
        }

    # Pipeline-level errors
    if "decompose" in detail.lower() and "false" in detail.lower():
        return {
            "error_domain": "pipeline",
            "root_cause_key": "decompose.false_positive",
            "prevention": "Validate cross-project change_dir existence before decomposing",
        }
    if "proposal" in detail.lower() and "empty" in detail.lower():
        return {
            "error_domain": "pipeline",
            "root_cause_key": "proposal.empty",
            "prevention": "Check proposal file content before processing",
        }

    # Default: code domain with unknown root cause
    return {
        "error_domain": "code",
        "root_cause_key": "unknown",
        "prevention": "review error and adjust approach",
    }


def record_success(
    change_name: str,
    project: str,
    phase_records: list[dict] = None,
    total_turns: int = 0,
    total_seconds: float = 0.0,
):
    """Record a successful change completion to learnings.jsonl."""
    # Calculate first_pass and fix_attempts from phase_records
    fix_attempts = 0
    if phase_records:
        for phase_rec in phase_records:
            fix_attempts += phase_rec.get("fix_attempts", 0)
    first_pass = fix_attempts == 0

    record = {
        "type": "success_pattern",
        "ts": datetime.now().isoformat(),
        "source": "orchestrator",
        "change_name": change_name,
        "project": project,
        "pattern_key": "pipeline.pass.deliver",
        "error_domain": "success",
        "first_pass": first_pass,
        "fix_attempts": fix_attempts,
        "total_turns": total_turns,
        "total_seconds": total_seconds,
        "severity": "low",
    }

    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    learnings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(learnings_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    try:
        from ..metrics.db import record_lesson as _db_record
        _db_record(
            text=f"success: {change_name} first_pass={first_pass} fix_attempts={fix_attempts} turns={total_turns}",
            pattern_key="pipeline.pass.deliver",
            category="success",
            ts=record["ts"],
        )
    except Exception:
        pass


def search_learnings(keywords: list[str], pattern_key: str | None = None) -> list[dict]:
    """Search learnings.jsonl by keywords with optional pattern_key filter.

    Returns entries ranked by number of unique keyword matches (descending),
    then by recency (most recent first). Each result includes a ``_score`` field.
    """
    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    if not learnings_file.exists():
        return []

    keywords_lower = [kw.lower() for kw in keywords]
    results: list[dict] = []

    with open(learnings_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if pattern_key is not None and entry.get("pattern_key") != pattern_key:
                continue

            searchable = " ".join(
                str(entry.get(field, ""))
                for field in ("title", "context", "takeaway")
            ).lower()

            matched = sum(1 for kw in keywords_lower if kw in searchable)
            if matched == 0:
                continue

            entry["_score"] = matched
            results.append(entry)

    # Sort: higher score first; within same score, newer (higher ts) first
    # Use stable multi-key sort: first by ts desc, then by score desc
    results.sort(key=lambda e: e.get("ts", ""), reverse=True)
    results.sort(key=lambda e: e["_score"], reverse=True)
    return results
