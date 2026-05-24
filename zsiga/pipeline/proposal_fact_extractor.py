"""Deterministic fact extraction from proposals.

Extracts file paths, function/method/class names, and variable names from proposal text,
then verifies their existence in the target codebase using grep/find (not LLM).
Produces a structured FactReport that can be injected into scout/steward prompts.
"""
import os
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FileFact:
    path: str
    exists: bool
    abs_path: str = ""
    defined_symbols: list[str] = field(default_factory=list)
    size_lines: int = 0


@dataclass
class SymbolFact:
    name: str
    kind: str  # "function", "class", "variable"
    defined_in: str = ""
    line_number: int = 0
    line_content: str = ""
    exists: bool = False
    close_matches: list[str] = field(default_factory=list)


@dataclass
class FactReport:
    mentioned_files: list[FileFact] = field(default_factory=list)
    mentioned_symbols: list[SymbolFact] = field(default_factory=list)
    files_exist_summary: str = ""
    symbols_exist_summary: str = ""

    def to_prompt_section(self) -> str:
        lines = ["## 确定性事实（由代码验证，不可质疑）", ""]
        if self.mentioned_files:
            lines.append("### 文件验证")
            for f in self.mentioned_files:
                status = "✅ 存在" if f.exists else "❌ 不存在"
                lines.append(f"- {f.path}: {status} ({f.size_lines} 行)")
                if f.exists and f.defined_symbols:
                    lines.append(f"  定义: {', '.join(f.defined_symbols[:15])}")
            lines.append("")

        if self.mentioned_symbols:
            lines.append("### 符号验证")
            for s in self.mentioned_symbols:
                if s.exists:
                    lines.append(
                        f"- {s.name} ({s.kind}): ✅ 定义于 {s.defined_in}:{s.line_number} — {s.line_content[:60]}"
                    )
                else:
                    close = f"  接近匹配: {', '.join(s.close_matches[:3])}" if s.close_matches else "  无接近匹配"
                    lines.append(f"- {s.name} ({s.kind}): ❌ 未找到定义。{close}")
            lines.append("")

        return "\n".join(lines) if len(lines) > 3 else ""


_STOPWORDS = frozenset({
    "the", "and", "for", "not", "this", "that", "with", "from", "into",
    "json", "dict", "curl", "time", "true", "field", "void", "add", "has",
    "get", "set", "put", "run", "use", "new", "can", "all", "may", "but",
    "out", "key", "api", "via", "file", "code", "test", "data", "list",
    "case", "need", "will", "also", "make", "more", "than", "then", "each",
    "when", "what", "how", "why", "who", "are", "was", "been", "have",
    "does", "should", "would", "could", "must", "shall", "only", "just",
    "like", "over", "such", "some", "very", "even", "back", "still",
    "work", "step", "call", "next", "last", "show", "part", "turn",
})


def extract_facts(proposal: str, target_path: str) -> FactReport:
    report = FactReport()

    file_paths = _extract_file_paths(proposal)
    symbols = _extract_symbols(proposal)

    for fp in file_paths:
        fact = _verify_file(fp, target_path)
        report.mentioned_files.append(fact)

    all_defined_in_files = {}
    for f in report.mentioned_files:
        if f.exists:
            all_defined_in_files[f.path] = f.defined_symbols

    for sym in symbols:
        fact = _verify_symbol(sym, target_path, report.mentioned_files)
        report.mentioned_symbols.append(fact)

    exist_count = sum(1 for f in report.mentioned_files if f.exists)
    total = len(report.mentioned_files)
    report.files_exist_summary = f"{exist_count}/{total} files exist"

    sym_exist = sum(1 for s in report.mentioned_symbols if s.exists)
    sym_total = len(report.mentioned_symbols)
    report.symbols_exist_summary = f"{sym_exist}/{sym_total} symbols found"

    return report


def _extract_file_paths(text: str) -> list[str]:
    patterns = re.findall(r"[\w/.]+\.py\b", text)
    patterns += re.findall(r"[\w/.]+\.rs\b", text)
    patterns += re.findall(r"[\w/.]+\.ts\b", text)
    patterns += re.findall(r"[\w/.]+\.yaml\b", text)
    patterns += re.findall(r"[\w/.]+\.toml\b", text)
    seen = set()
    result = []
    for p in patterns:
        p = p.lstrip("/")
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _extract_symbols(text: str) -> list[str]:
    idents = set(re.findall(r"\b([a-z_][a-z0-9_]{2,})\b", text))
    code_like = [i for i in idents if i not in _STOPWORDS and len(i) > 4]
    code_like += re.findall(r"\b(_[a-z][a-z0-9_]+)\b", text)
    return list(set(code_like))


def _verify_file(rel_path: str, target_path: str) -> FileFact:
    abs_path = os.path.join(target_path, rel_path)
    exists = os.path.isfile(abs_path)
    fact = FileFact(path=rel_path, exists=exists, abs_path=abs_path)

    if exists:
        with open(abs_path) as f:
            content = f.read()
        fact.size_lines = len(content.split("\n"))
        funcs = re.findall(r"^def (\w+)", content, re.MULTILINE)
        classes = re.findall(r"^class (\w+)", content, re.MULTILINE)
        fact.defined_symbols = funcs + classes

    return fact


def _verify_symbol(name: str, target_path: str, file_facts: list[FileFact]) -> SymbolFact:
    fact = SymbolFact(name=name, kind="unknown")

    search_dirs = [target_path]
    for ff in file_facts:
        if ff.exists:
            search_dirs.append(os.path.dirname(ff.abs_path))

    for search_dir in set(search_dirs):
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d not in {"venv", ".git", "__pycache__", "node_modules"}]
            for fname in files:
                if not fname.endswith((".py", ".rs", ".ts")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath) as f:
                        for i, line in enumerate(f, 1):
                            stripped = line.strip()
                            if f"def {name}" in stripped:
                                rel = os.path.relpath(fpath, target_path)
                                fact.exists = True
                                fact.defined_in = rel
                                fact.line_number = i
                                fact.line_content = stripped[:80]
                                fact.kind = "function"
                                return fact
                            if f"class {name}" in stripped:
                                rel = os.path.relpath(fpath, target_path)
                                fact.exists = True
                                fact.defined_in = rel
                                fact.line_number = i
                                fact.line_content = stripped[:80]
                                fact.kind = "class"
                                return fact
                except (OSError, UnicodeDecodeError):
                    continue

    _find_close_matches(fact, name, target_path, file_facts)
    return fact


def _find_close_matches(fact: SymbolFact, name: str, target_path: str, file_facts: list[FileFact]):
    prefix = name[:4]
    for ff in file_facts:
        if ff.exists and ff.defined_symbols:
            close = [s for s in ff.defined_symbols if prefix in s or s[:4] in name]
            if close:
                fact.close_matches = close[:5]
                return
