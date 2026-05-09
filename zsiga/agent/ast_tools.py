import os
from ast_grep_py import SgRoot
from ..transport import Transport, LocalTransport

LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "javascript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".rb": "ruby",
    ".html": "html",
    ".css": "css",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
}


def _detect_lang(path: str) -> str | None:
    _, ext = os.path.splitext(path)
    return LANG_MAP.get(ext)


def _read_source(transport: Transport, target_path: str, path: str) -> str | None:
    if path.startswith(target_path):
        path = path[len(target_path):].lstrip("/")
    full = f"{target_path}/{path}"
    try:
        if isinstance(transport, LocalTransport):
            from pathlib import Path
            p = Path(full)
            if not p.exists():
                return None
            return p.read_text(errors="replace")
        else:
            r = transport.run_shell(f"cat '{full}'")
            if r["exit_code"] != 0:
                return None
            return r["stdout"]
    except Exception:
        return None


def _write_source(transport: Transport, target_path: str, path: str, content: str):
    if path.startswith(target_path):
        path = path[len(target_path):].lstrip("/")
    full = f"{target_path}/{path}"
    if isinstance(transport, LocalTransport):
        from pathlib import Path
        Path(full).write_text(content)
    else:
        transport.run_shell(f"cat > '{full}'", stdin_data=content)


def ast_search(transport: Transport, target_path: str,
               pattern: str, path: str, lang: str = None) -> dict:
    lang = lang or _detect_lang(path)
    if not lang:
        return {"error": f"Cannot detect language for {path}. Specify lang parameter."}

    source = _read_source(transport, target_path, path)
    if source is None:
        return {"error": f"File not found: {path}"}

    try:
        root = SgRoot(source, lang)
        node = root.root()
        matches = list(node.find_all(pattern=pattern))
    except Exception as e:
        return {"error": f"AST parse error: {e}"}

    results = []
    for m in matches[:50]:
        r = m.range()
        results.append({
            "text": m.text(),
            "start_line": r.start.line + 1,
            "start_col": r.start.column + 1,
            "end_line": r.end.line + 1,
            "end_col": r.end.column + 1,
        })

    return {"matches": len(results), "results": results, "file": path, "lang": lang}


def ast_replace(transport: Transport, target_path: str,
                pattern: str, replacement: str, path: str,
                lang: str = None) -> dict:
    lang = lang or _detect_lang(path)
    if not lang:
        return {"error": f"Cannot detect language for {path}. Specify lang parameter."}

    source = _read_source(transport, target_path, path)
    if source is None:
        return {"error": f"File not found: {path}"}

    try:
        root = SgRoot(source, lang)
        node = root.root()
        matches = list(node.find_all(pattern=pattern))
    except Exception as e:
        return {"error": f"AST parse error: {e}"}

    if not matches:
        return {"error": f"Pattern not found: {pattern}", "matches": 0}

    edits = []
    for m in matches:
        edit = m.replace(replacement)
        edits.append(edit)

    new_source = node.commit_edits(edits)
    _write_source(transport, target_path, path, new_source)

    return {
        "ok": True,
        "matches_replaced": len(matches),
        "file": path,
        "lang": lang,
    }
