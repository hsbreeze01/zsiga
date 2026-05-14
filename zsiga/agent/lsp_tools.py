"""LSP 级代码感知工具 — goto_definition, find_references, diagnostics

本地 transport 使用 jedi 提供精确的 LSP 功能。
远程 transport 使用 grep + ruff/pyflakes 作为 fallback。
"""
from pathlib import Path

from ..transport import Transport, LocalTransport

# ---------------------------------------------------------------------------
# 读取源码（复用 ast_tools 的模式）
# ---------------------------------------------------------------------------

def _resolve_path(target_path: str, path: str) -> str:
    if path.startswith(target_path):
        path = path[len(target_path):].lstrip("/")
    return path


def _read_source(transport: Transport, target_path: str, path: str) -> str | None:
    path = _resolve_path(target_path, path)
    full = f"{target_path}/{path}"
    try:
        if isinstance(transport, LocalTransport):
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


# ---------------------------------------------------------------------------
# 本地实现（jedi）
# ---------------------------------------------------------------------------

def _jedi_goto(transport: Transport, target_path: str, path: str,
               line: int, column: int) -> dict:
    source = _read_source(transport, target_path, path)
    if source is None:
        return {"error": f"File not found: {path}"}

    try:
        import jedi
    except ImportError:
        return {"error": "jedi not installed. Run: pip install jedi"}

    full = f"{target_path}/{_resolve_path(target_path, path)}"
    try:
        script = jedi.Script(source, path=full)
        defs = script.goto(line=line, column=column)
    except Exception as e:
        return {"error": f"jedi goto failed: {e}"}

    results = []
    for d in defs:
        mod = str(d.module_path) if d.module_path else None
        # 把绝对路径转回相对路径
        if mod and mod.startswith(target_path):
            mod = mod[len(target_path):].lstrip("/")
        results.append({
            "name": d.name,
            "module_path": mod,
            "line": d.line,
            "column": d.column,
            "description": d.description,
        })

    return {"definitions": len(results), "results": results}


def _jedi_references(transport: Transport, target_path: str, path: str,
                     line: int, column: int) -> dict:
    source = _read_source(transport, target_path, path)
    if source is None:
        return {"error": f"File not found: {path}"}

    try:
        import jedi
    except ImportError:
        return {"error": "jedi not installed. Run: pip install jedi"}

    full = f"{target_path}/{_resolve_path(target_path, path)}"
    try:
        script = jedi.Script(source, path=full)
        refs = script.get_references(line=line, column=column)
    except Exception as e:
        return {"error": f"jedi references failed: {e}"}

    results = []
    for r in refs:
        mod = str(r.module_path) if r.module_path else None
        if mod and mod.startswith(target_path):
            mod = mod[len(target_path):].lstrip("/")
        results.append({
            "name": r.name,
            "module_path": mod,
            "line": r.line,
            "column": r.column,
        })

    # 过滤：只保留项目内的引用（排除 stdlib 和 site-packages）
    project_refs = [
        r for r in results
        if r["module_path"] and not r["module_path"].startswith("/opt/")
        and not r["module_path"].startswith("/usr/")
        and not r["module_path"].startswith("/Library/")
    ]

    return {
        "references": len(project_refs),
        "total_including_external": len(results),
        "results": project_refs[:50],
    }


def _jedi_diagnostics(transport: Transport, target_path: str, path: str) -> dict:
    source = _read_source(transport, target_path, path)
    if source is None:
        return {"error": f"File not found: {path}"}

    try:
        import jedi
    except ImportError:
        return {"error": "jedi not installed. Run: pip install jedi"}

    full = f"{target_path}/{_resolve_path(target_path, path)}"
    errors = []

    # 语法错误
    try:
        script = jedi.Script(source, path=full)
        for e in script.get_syntax_errors():
            errors.append({
                "type": "syntax_error",
                "message": f"Syntax error at line {e.line}",
                "line": e.line,
                "column": e.column,
                "until_line": e.until_line,
                "until_column": e.until_column,
            })
    except Exception as e:
        errors.append({
            "type": "parse_error",
            "message": f"Failed to parse: {e}",
            "line": 0,
            "column": 0,
        })

    # ruff 静态检查（如果可用）
    _add_ruff_diagnostics(transport, target_path, path, errors)

    return {"errors": len(errors), "results": errors}


# ---------------------------------------------------------------------------
# 远程 fallback（grep + ruff）
# ---------------------------------------------------------------------------

def _grep_goto(transport: Transport, target_path: str, path: str,
               line: int, column: int) -> dict:
    """grep-based goto_definition：读取指定行，提取符号名，搜索定义"""
    source = _read_source(transport, target_path, path)
    if source is None:
        return {"error": f"File not found: {path}"}

    lines = source.split("\n")
    if line < 1 or line > len(lines):
        return {"error": f"Line {line} out of range (1-{len(lines)})"}

    target_line = lines[line - 1]
    # 提取光标位置的标识符
    if column > len(target_line):
        column = len(target_line)

    # 向左向右扩展获取完整标识符
    start = column - 1  # 0-based
    while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == '_'):
        start -= 1
    end = column - 1
    while end < len(target_line) and (target_line[end].isalnum() or target_line[end] == '_'):
        end += 1

    symbol = target_line[start:end]
    if not symbol:
        return {"error": f"No symbol at line {line}, column {column}"}

    # 搜索定义：def symbol, class symbol, symbol = 
    import re
    def_patterns = [
        rf"(def|class)\s+{re.escape(symbol)}\b",
        rf"^{re.escape(symbol)}\s*=",
    ]
    results = []
    for pattern in def_patterns:
        r = transport.run_shell(
            f"grep -rn -E '{pattern}' '{target_path}' --include='*.py' | head -20",
            timeout=30,
        )
        if r["exit_code"] == 0:
            for grep_line in r["stdout"].strip().split("\n"):
                if ":" not in grep_line:
                    continue
                parts = grep_line.split(":", 2)
                if len(parts) >= 3:
                    fpath = parts[0]
                    if fpath.startswith(target_path):
                        fpath = fpath[len(target_path):].lstrip("/")
                    results.append({
                        "name": symbol,
                        "module_path": fpath,
                        "line": int(parts[1]),
                        "column": 0,
                        "description": parts[2].strip()[:100],
                    })

    return {"definitions": len(results), "results": results[:20]}


def _grep_references(transport: Transport, target_path: str, path: str,
                     line: int, column: int) -> dict:
    """grep-based find_references：提取符号名，全项目搜索"""
    source = _read_source(transport, target_path, path)
    if source is None:
        return {"error": f"File not found: {path}"}

    lines = source.split("\n")
    if line < 1 or line > len(lines):
        return {"error": f"Line {line} out of range"}

    target_line = lines[line - 1]
    if column > len(target_line):
        column = len(target_line)

    start = column - 1
    while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == '_'):
        start -= 1
    end = column - 1
    while end < len(target_line) and (target_line[end].isalnum() or target_line[end] == '_'):
        end += 1

    symbol = target_line[start:end]
    if not symbol:
        return {"error": f"No symbol at line {line}, column {column}"}

    import re
    # 搜索所有引用（排除注释行）
    pattern = rf"\b{re.escape(symbol)}\b"
    r = transport.run_shell(
        f"grep -rn -E '{pattern}' '{target_path}' --include='*.py' | grep -v '#.*{re.escape(symbol)}' | head -50",
        timeout=30,
    )

    results = []
    if r["exit_code"] == 0:
        for grep_line in r["stdout"].strip().split("\n"):
            if ":" not in grep_line:
                continue
            parts = grep_line.split(":", 2)
            if len(parts) >= 3:
                fpath = parts[0]
                if fpath.startswith(target_path):
                    fpath = fpath[len(target_path):].lstrip("/")
                results.append({
                    "name": symbol,
                    "module_path": fpath,
                    "line": int(parts[1]),
                    "column": 0,
                })

    return {"references": len(results), "results": results[:50]}


# ---------------------------------------------------------------------------
# ruff diagnostics（local + remote 通用）
# ---------------------------------------------------------------------------

def _add_ruff_diagnostics(transport: Transport, target_path: str, path: str,
                          errors: list):
    """追加 ruff check 结果到 errors 列表"""
    rel_path = _resolve_path(target_path, path)
    ruff_cmd = f"ruff check '{rel_path}' --output-format=json 2>/dev/null"

    try:
        r = transport.run_shell(ruff_cmd, cwd=target_path, timeout=30)
    except Exception:
        return

    if r.get("exit_code", -1) != 0 or not r.get("stdout"):
        return

    try:
        import json
        items = json.loads(r["stdout"])
    except Exception:
        return

    for item in items[:30]:
        errors.append({
            "type": "lint",
            "code": item.get("code", ""),
            "message": item.get("message", ""),
            "line": item.get("location", {}).get("row", 0),
            "column": item.get("location", {}).get("column", 0),
            "fixable": item.get("fix", {}).get("applicable", False),
        })


# ---------------------------------------------------------------------------
# 公开 API（transport 分发）
# ---------------------------------------------------------------------------

def lsp_goto_definition(transport: Transport, target_path: str, path: str,
                        line: int, column: int) -> dict:
    """跳转到定义：给定文件/行/列，找到符号的定义位置"""
    if isinstance(transport, LocalTransport):
        return _jedi_goto(transport, target_path, path, line, column)
    return _grep_goto(transport, target_path, path, line, column)


def lsp_find_references(transport: Transport, target_path: str, path: str,
                        line: int, column: int) -> dict:
    """查找引用：给定文件/行/列，找到符号在项目中的所有引用"""
    if isinstance(transport, LocalTransport):
        return _jedi_references(transport, target_path, path, line, column)
    return _grep_references(transport, target_path, path, line, column)


def lsp_diagnostics(transport: Transport, target_path: str, path: str) -> dict:
    """诊断：检查文件的语法错误和 lint 问题"""
    if isinstance(transport, LocalTransport):
        return _jedi_diagnostics(transport, target_path, path)

    # 远程：纯 ruff + 语法检查
    errors = []
    _add_ruff_diagnostics(transport, target_path, path, errors)

    # 远程 Python 语法检查
    rel_path = _resolve_path(target_path, path)
    r = transport.run_shell(
        f"python3 -c \"import py_compile; py_compile.compile('{rel_path}', doraise=True)\" 2>&1",
        cwd=target_path, timeout=15,
    )
    if r["exit_code"] != 0 and "SyntaxError" in r.get("stderr", ""):
        import re
        m = re.search(r"line (\d+)", r["stderr"])
        errors.append({
            "type": "syntax_error",
            "message": r["stderr"].strip()[:200],
            "line": int(m.group(1)) if m else 0,
            "column": 0,
        })

    return {"errors": len(errors), "results": errors}
