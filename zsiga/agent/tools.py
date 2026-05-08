import json
import os
import subprocess
from pathlib import Path

from ..transport import Transport, LocalTransport


def _bash(transport: Transport, target_path, command, timeout=120):
    r = transport.run_shell(command, cwd=target_path, timeout=timeout)
    return {
        "exit_code": r["exit_code"],
        "stdout": r["stdout"][-10000:],
        "stderr": r["stderr"][-3000:],
    }


def _read_file(transport: Transport, target_path, path):
    if path.startswith(target_path):
        path = path[len(target_path):].lstrip("/")
    full = f"{target_path}/{path}"
    if isinstance(transport, LocalTransport):
        full_path = Path(full)
        if not full_path.exists():
            return {"error": f"File not found: {path}"}
        content = full_path.read_text(errors="replace")
    else:
        r = transport.run_shell(f"cat '{full}'")
        if r["exit_code"] != 0:
            return {"error": f"File not found: {path}"}
        content = r["stdout"]
    return {"path": path, "content": content, "lines": content.count("\n") + 1}


def _write_file(transport: Transport, target_path, path, content):
    # Handle LLM passing absolute paths — strip target_path prefix if present
    if path.startswith(target_path):
        path = path[len(target_path):].lstrip("/")
    full = f"{target_path}/{path}"
    if isinstance(transport, LocalTransport):
        full_path = Path(full)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    else:
        transport.run_shell(f"mkdir -p $(dirname '{full}')")
        r = transport.run_shell(f"cat > '{full}'", stdin_data=content)
        if r["exit_code"] != 0:
            return {"error": f"Write failed: {r['stderr']}"}
    return {"ok": True, "path": path, "bytes": len(content)}


def _edit_file(transport: Transport, target_path, path, old_text, new_text):
    if path.startswith(target_path):
        path = path[len(target_path):].lstrip("/")
    full = f"{target_path}/{path}"
    if isinstance(transport, LocalTransport):
        full_path = Path(full)
        if not full_path.exists():
            return {"error": f"File not found: {path}"}
        content = full_path.read_text()
    else:
        r = transport.run_shell(f"cat '{full}'")
        if r["exit_code"] != 0:
            return {"error": f"File not found: {path}"}
        content = r["stdout"]

    if old_text not in content:
        return {"error": f"old_text not found in {path}"}
    if content.count(old_text) > 1:
        return {"error": f"old_text found {content.count(old_text)} times in {path}, must be unique"}
    content = content.replace(old_text, new_text)

    if isinstance(transport, LocalTransport):
        Path(full).write_text(content)
    else:
        transport.run_shell(f"cat > '{full}'", stdin_data=content)
    return {"ok": True, "path": path}


def _search(transport: Transport, target_path, pattern, include=None):
    if isinstance(transport, LocalTransport):
        cmd = ["grep", "-rn", "-E", pattern]
        if include:
            cmd.extend(["--include", include])
        cmd.append(target_path)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = r.stdout
    else:
        grep_cmd = f"grep -rn -E '{pattern}'"
        if include:
            grep_cmd += f" --include='{include}'"
        grep_cmd += f" '{target_path}'"
        r = transport.run_shell(grep_cmd, timeout=30)
        output = r.get("stdout", "")

    lines = output.strip().split("\n")[:100]
    results = []
    for line in lines:
        if ":" in line:
            parts = line.split(":", 2)
            if len(parts) >= 3:
                results.append({"file": parts[0], "line": parts[1], "text": parts[2][:200]})
    return {"matches": len(results), "results": results[:50]}


def _list_files(transport: Transport, target_path, path=""):
    full = f"{target_path}/{path}".rstrip("/")
    if isinstance(transport, LocalTransport):
        full_path = Path(full)
        if not full_path.is_dir():
            return {"error": f"Not a directory: {path}"}
        entries = []
        for p in sorted(full_path.iterdir())[:200]:
            rel = p.relative_to(target_path)
            entries.append({"name": rel.as_posix(), "is_dir": p.is_dir()})
        return {"entries": entries}
    else:
        r = transport.run_shell(
            f"ls -la --time-style=+ '{full}' 2>/dev/null | tail -n +2 || echo '__NOTDIR__'",
            timeout=15,
        )
        output = r.get("stdout", "").strip()
        if "__NOTDIR__" in output or r["exit_code"] != 0:
            return {"error": f"Not a directory: {path}"}
        entries = []
        for line in output.split("\n")[:200]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 7:
                continue
            name = parts[-1]
            if name in (".", ".."):
                continue
            is_dir = parts[0].startswith("d")
            rel = f"{path}/{name}".lstrip("/") if path else name
            entries.append({"name": rel, "is_dir": is_dir})
        return {"entries": entries}


def register_tools(agent, target_path: str, transport: Transport = None):
    transport = transport or LocalTransport()
    agent.tools = []
    agent.tool_funcs = {}

    agent.register_tool(
        name="bash",
        description="在目标项目中执行 shell 命令",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell 命令"},
                "timeout": {"type": "integer", "description": "超时秒数"},
            },
            "required": ["command"],
        },
        func=lambda command, timeout=120: _bash(transport, target_path, command, timeout),
    )

    agent.register_tool(
        name="read_file",
        description="读取目标项目的文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对目标项目根目录）"},
            },
            "required": ["path"],
        },
        func=lambda path: _read_file(transport, target_path, path),
    )

    agent.register_tool(
        name="write_file",
        description="在目标项目中创建或覆盖文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        func=lambda path, content: _write_file(transport, target_path, path, content),
    )

    agent.register_tool(
        name="edit_file",
        description="精确替换文件中的文本片段（old_text 必须在文件中唯一匹配）",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string", "description": "要替换的原文（必须精确匹配）"},
                "new_text": {"type": "string", "description": "替换后的新文本"},
            },
            "required": ["path", "old_text", "new_text"],
        },
        func=lambda path, old_text, new_text: _edit_file(transport, target_path, path, old_text, new_text),
    )

    agent.register_tool(
        name="search",
        description="正则搜索目标项目文件内容",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "正则表达式"},
                "include": {"type": "string", "description": "文件过滤，如 *.py"},
            },
            "required": ["pattern"],
        },
        func=lambda pattern, include=None: _search(transport, target_path, pattern, include),
    )

    agent.register_tool(
        name="list_files",
        description="列出目标项目的目录结构",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "目录路径（相对目标项目根目录）"},
            },
            "required": [],
        },
        func=lambda path="": _list_files(transport, target_path, path),
    )
