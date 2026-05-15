import json
from datetime import datetime
from pathlib import Path

from ..metrics.db import write_journal_entry as _db_write
from ..metrics.db import load_journal as _db_load

_MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "memory"


def write_entry(text: str, mood: str = "note", author: str = "Sisyphus"):
    valid_moods = {"praise", "criticism", "milestone", "learned", "note"}
    if mood not in valid_moods:
        mood = "note"

    _db_write(text=text, mood=mood, author=author)

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
    return _db_load(limit=limit)
