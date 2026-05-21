import json
import logging
import re
from datetime import datetime
from pathlib import Path

_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"

_BLACKLISTED_PREFIXES = ("daemon.cycle_error",)

_LOGGER = logging.getLogger(__name__)


def _is_blacklisted(pattern_key: str | None) -> bool:
    if not pattern_key:
        return False
    return any(pattern_key.startswith(prefix) for prefix in _BLACKLISTED_PREFIXES)


def _text_too_short(text: str) -> bool:
    return not text or len(text.strip()) < 10


def record_lesson(title: str, context: str, takeaway: str,
                  pattern_key: str = None, source: str = "pipeline"):
    if _is_blacklisted(pattern_key):
        _LOGGER.debug("Skipping lesson: pattern_blacklisted (%s)", pattern_key)
        return
    if _text_too_short(takeaway):
        _LOGGER.debug("Skipping lesson: text_too_short (pattern_key=%s)", pattern_key)
        return

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

    if _is_blacklisted(pattern_key):
        _LOGGER.debug("Skipping outcome: pattern_blacklisted (%s)", pattern_key)
        return
    if _text_too_short(prevention):
        _LOGGER.debug("Skipping outcome: text_too_short (pattern_key=%s)", pattern_key)
        return

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
    pattern_key = "pipeline.pass.deliver"

    if _is_blacklisted(pattern_key):
        _LOGGER.debug("Skipping success: pattern_blacklisted (%s)", pattern_key)
        return

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
        "pattern_key": pattern_key,
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


def fetch_relevant_learnings(
    change_name: str,
    max_count: int = 5,
    learnings_file: Path | None = None,
) -> str:
    """Fetch relevant learnings for prompt injection.

    Reads ``memory/learnings.jsonl``, filters entries by relevance to the
    given change context, and returns the most recent *max_count* entries
    as formatted markdown text.

    Relevance rules:
    1. **Direct match**: entry's ``pattern_key`` contains a keyword from
       *change_name* (after splitting on ``-`` and ``_``).
    2. **Pipeline category**: entry's ``pattern_key`` starts with
       ``pipeline.fail.`` or ``pipeline.pass.``.

    Each matching entry is formatted as ``- [{pattern_key}] {takeaway}``.

    Returns an empty string when no entries match.
    """
    lf = learnings_file or (_MEMORY_DIR / "learnings.jsonl")
    if not lf.exists():
        return ""

    # Extract keywords from change_name
    keywords = set(
        kw.lower()
        for kw in re.split(r"[-_]+", change_name)
        if len(kw) >= 2
    )

    candidates: list[dict] = []
    with open(lf, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            takeaway = entry.get("takeaway", "")
            if not takeaway or not takeaway.strip():
                continue

            pk = entry.get("pattern_key", "")
            if not pk:
                continue

            # Check relevance
            is_relevant = False

            # Rule 1: direct name match
            pk_lower = pk.lower()
            if any(kw in pk_lower for kw in keywords):
                is_relevant = True

            # Rule 2: pipeline category
            if pk.startswith("pipeline.fail.") or pk.startswith("pipeline.pass."):
                is_relevant = True

            if is_relevant:
                candidates.append(entry)

    if not candidates:
        return ""

    # Sort by ts descending
    candidates.sort(key=lambda e: e.get("ts", ""), reverse=True)
    candidates = candidates[:max_count]

    lines = [f"- [{e.get('pattern_key', '')}] {e.get('takeaway', '')}" for e in candidates]
    return "\n".join(lines)


_NOISY_PATTERN_KEYS = {"daemon.cycle_error", "code.unknown"}


def cleanup_learnings_jsonl(
    learnings_file: Path | None = None,
) -> dict:
    """Remove noisy entries from learnings.jsonl.

    Removes records where:
    - ``takeaway`` (or ``text`` for legacy entries) is empty / whitespace-only
    - ``pattern_key`` equals ``daemon.cycle_error`` or ``code.unknown``

    Returns a summary dict with keys ``removed`` (int) and ``kept`` (int).
    """
    lf = learnings_file or (_MEMORY_DIR / "learnings.jsonl")
    if not lf.exists():
        return {"removed": 0, "kept": 0}

    kept: list[str] = []
    removed = 0

    with open(lf, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue

            pk = entry.get("pattern_key", "")

            # Check blacklisted pattern keys
            if pk in _NOISY_PATTERN_KEYS:
                removed += 1
                continue

            # Check empty takeaway/text
            takeaway = entry.get("takeaway", "")
            text = entry.get("text", "")
            primary = takeaway or text
            if not primary or not primary.strip():
                removed += 1
                continue

            kept.append(raw)

    with open(lf, "w", encoding="utf-8") as f:
        for entry_line in kept:
            f.write(entry_line + "\n")

    _LOGGER.info(
        "cleanup_learnings_jsonl: removed=%d, kept=%d", removed, len(kept)
    )
    return {"removed": removed, "kept": len(kept)}
