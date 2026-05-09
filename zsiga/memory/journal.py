import json
from datetime import datetime
from pathlib import Path

_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"


def write_entry(text: str, mood: str = "note", author: str = "Sisyphus"):
    """Append a growth journal entry.

    Args:
        text: Free-form observation about zsiga (praise, criticism, milestone).
        mood: One of "praise" (positive), "criticism" (needs improvement),
              "milestone" (achievement unlocked), "note" (neutral).
        author: Who wrote this entry.
    """
    valid_moods = {"praise", "criticism", "milestone", "learned", "note"}
    if mood not in valid_moods:
        mood = "note"

    entry = {
        "ts": datetime.now().isoformat(),
        "mood": mood,
        "author": author,
        "text": text,
    }

    journal_file = _MEMORY_DIR / "journal.jsonl"
    journal_file.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_journal(limit: int = 0) -> list[dict]:
    journal_file = _MEMORY_DIR / "journal.jsonl"
    if not journal_file.exists():
        return []
    lines = [
        json.loads(l) for l in
        journal_file.read_text(encoding="utf-8").strip().split("\n")
        if l.strip()
    ]
    if limit > 0:
        lines = lines[-limit:]
    return lines
