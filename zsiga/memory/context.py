import json
from pathlib import Path

_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"


def load_active_context() -> str:
    ctx_file = _MEMORY_DIR / "active_context.md"
    if not ctx_file.exists():
        return ""
    return ctx_file.read_text(encoding="utf-8").strip()


def update_active_context(new_lessons: list[str] = None):
    ctx_file = _MEMORY_DIR / "active_context.md"
    existing = ""
    if ctx_file.exists():
        existing = ctx_file.read_text(encoding="utf-8")

    lessons_text = ""
    if new_lessons:
        lessons_text = "\n\n## Recent Lessons\n" + "\n".join(
            f"- {l}" for l in new_lessons
        )

    base = _build_base_context()
    ctx_file.parent.mkdir(parents=True, exist_ok=True)
    ctx_file.write_text(base + lessons_text + "\n", encoding="utf-8")


def load_recent_lessons(n: int = 20) -> list[str]:
    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    if not learnings_file.exists():
        return []
    lines = learnings_file.read_text(encoding="utf-8").strip().split("\n")
    lines = [l for l in lines if l.strip()]
    if not lines:
        return []
    recent = lines[-n:]
    lessons = []
    for line in recent:
        try:
            obj = json.loads(line)
            # Prefer structured rule over fuzzy takeaway
            if obj.get("rule"):
                rule = obj["rule"]
                case_what = obj.get("case", {}).get("what", "")
                if case_what:
                    lessons.append(f"[RULE] {rule} (case: {case_what[:80]})")
                else:
                    lessons.append(f"[RULE] {rule}")
            else:
                pk = obj.get("pattern_key", "")
                tw = obj.get("takeaway", "")
                lessons.append(f"[{pk}] {tw}" if pk else tw)
        except json.JSONDecodeError:
            continue
    return lessons


def _build_base_context() -> str:
    parts = [
        "# zsiga Active Context",
        "",
        "## Identity",
        "zsiga is an independent autonomous agent. It operates on external projects through OpenSpec-driven development.",
        "",
        "## Principles",
        "- OpenSpec specs are the single source of truth",
        "- Every change must pass pytest + ruff before commit",
        "- Revert on failure, never leave code broken",
        "- Follow existing project patterns",
    ]

    # Inject target manifest for external projects
    try:
        from ..config import load_config
        cfg = load_config()
        for _tname, target in cfg.targets.items():
            if target.domain == "external":
                parts.append(f"\n## Target: {_tname}")
                if target.description:
                    parts.append(f"**Description**: {target.description}")
                if target.tech_stack:
                    parts.append(f"**Tech Stack**: {', '.join(target.tech_stack)}")
                if target.key_dirs:
                    parts.append(f"**Key Dirs**: {', '.join(target.key_dirs)}")
                if target.conventions:
                    parts.append(f"**Conventions**: {target.conventions}")
                parts.append(f"**Path**: {target.path}")
                parts.append(f"**Branch**: {target.deploy_branch}")
                break
    except Exception:
        pass

    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    if learnings_file.exists():
        lines = learnings_file.read_text(encoding="utf-8").strip().split("\n")
        lines = [l for l in lines if l.strip()]
        parts.append(f"\n## Session History: {len(lines)} lessons recorded")

    from .pattern_miner import mine_patterns, generate_warnings
    patterns = mine_patterns()
    if patterns:
        parts.append(generate_warnings(patterns))

    return "\n".join(parts)
