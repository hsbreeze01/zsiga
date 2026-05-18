"""Glossary extraction and caching for project terminology."""
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path

from ..transport import Transport, LocalTransport
from .utils import read_file

_GLOSSARY_DIR = Path(__file__).resolve().parent.parent / "memory" / "glossary"
_CACHE_TTL_HOURS = 24


@dataclass
class GlossaryEntry:
    name: str
    category: str  # class | function | route | config
    file: str


@dataclass
class Glossary:
    project: str
    extracted_at: str
    entries: list[GlossaryEntry] = field(default_factory=list)

    def summary(self, top_n: int = 30) -> str:
        if not self.entries:
            return ""
        by_cat: dict[str, list[str]] = {}
        for e in self.entries:
            by_cat.setdefault(e.category, []).append(e.name)
        lines = ["## Domain Glossary"]
        count = 0
        for cat, names in by_cat.items():
            if count >= top_n:
                break
            show = names[:top_n - count]
            lines.append(f"**{cat}**: {', '.join(show)}")
            count += len(show)
        return "\n".join(lines)


def _glossary_path(project_name: str) -> Path:
    return _GLOSSARY_DIR / f"{project_name}.json"


def load_glossary(project_name: str, target_path: str = None,
                  transport: Transport = None) -> Glossary | None:
    """Load cached glossary if fresh (< 24h), otherwise re-extract."""
    cache_path = _glossary_path(project_name)
    if cache_path.exists():
        try:
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
            extracted_at = datetime.fromisoformat(raw["extracted_at"])
            if datetime.now() - extracted_at < timedelta(hours=_CACHE_TTL_HOURS):
                entries = [GlossaryEntry(**e) for e in raw.get("entries", [])]
                return Glossary(project=raw["project"],
                                extracted_at=raw["extracted_at"],
                                entries=entries)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
    if target_path:
        return extract_glossary(target_path, transport)
    return None


def extract_glossary(target_path: str, transport: Transport = None) -> Glossary:
    """Scan project files and extract domain terminology."""
    transport = transport or LocalTransport()
    project_name = Path(target_path).name
    entries: list[GlossaryEntry] = []

    r = transport.run_shell(
        f"find '{target_path}' -name '*.py' "
        f"-not -path '*/venv/*' -not -path '*/__pycache__/*' "
        f"-not -path '*/.git/*' -not -path '*/site-packages/*' "
        f"| sort | head -200",
        timeout=15,
    )
    if r["exit_code"] != 0 or not r["stdout"].strip():
        return Glossary(project=project_name,
                        extracted_at=datetime.now().isoformat(),
                        entries=[])

    files = [f.strip() for f in r["stdout"].strip().split("\n") if f.strip()]
    for fpath in files:
        rel = fpath.replace(f"{target_path}/", "") if fpath.startswith(target_path) else fpath
        content = read_file(fpath, transport)
        if not content:
            continue
        entries.extend(_extract_from_content(content, rel))

    glossary = Glossary(
        project=project_name,
        extracted_at=datetime.now().isoformat(),
        entries=entries,
    )
    _save_glossary(glossary)
    return glossary


def _extract_from_content(content: str, rel_path: str) -> list[GlossaryEntry]:
    entries = []
    # Top-level class definitions
    for m in re.finditer(r"^class\s+([A-Z]\w+)", content, re.MULTILINE):
        entries.append(GlossaryEntry(name=m.group(1), category="class", file=rel_path))
    # Public function definitions (not _ prefixed)
    for m in re.finditer(r"^def\s+([a-zA-Z]\w+)", content, re.MULTILINE):
        entries.append(GlossaryEntry(name=m.group(1), category="function", file=rel_path))
    # Route decorator paths
    for m in re.finditer(r"@.*\.route\s*\(\s*['\"]([^'\"]+)['\"]", content):
        entries.append(GlossaryEntry(name=m.group(1), category="route", file=rel_path))
    # Config key patterns (uppercase assignments at module level)
    for m in re.finditer(r"^([A-Z][A-Z_]{2,})\s*=", content, re.MULTILINE):
        entries.append(GlossaryEntry(name=m.group(1), category="config", file=rel_path))
    return entries


def _save_glossary(glossary: Glossary):
    _GLOSSARY_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _glossary_path(glossary.project)
    data = {
        "project": glossary.project,
        "extracted_at": glossary.extracted_at,
        "entries": [asdict(e) for e in glossary.entries],
    }
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                          encoding="utf-8")
