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
    status = "PASS" if success else "FAIL"
    title = f"{status}: {change_name} at {phase}"
    ctx = f"project={project}, phase={phase}"
    if detail:
        ctx += f", detail={detail[:300]}"
    takeaway = ("Success" if success
                else f"Failed at {phase}: {detail[:200]}" if detail
                else f"Failed at {phase}")
    pattern_key = f"pipeline.{status.lower()}.{phase}"
    record_lesson(title, ctx, takeaway, pattern_key, source="orchestrator")
