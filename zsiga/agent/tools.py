import json
import subprocess
import re
from pathlib import Path


def _bash(target_path, command, timeout=120):
    r = subprocess.run(
        command, shell=True,
        cwd=target_path,
        capture_output=True, text=True,
        timeout=timeout,
    )
    return {
        "exit_code": r.returncode,
        "stdout": r.stdout[-10000:],
        "stderr": r.stderr[-3000:],
    }


def _read_file(target_path, path):
    full = Path(target_path) / path
    if not full.exists():
        return {"error": f"File not found: {path}"}
    content = full.read_text(errors="replace")
    return {"path": path, "content": content, "lines": content.count("\n") + 1}


def _write_file(target_path, path, content):
    full = Path(target_path) / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    return {"ok": True, "path": path, "bytes": len(content)}


def _edit_file(target_path, path, old_text, new_text):
    full = Path(target_path) / path
    if not full.exists():
        return {"error": f"File not found: {path}"}
    content = full.read_text()
    if old_text not in content:
        return {"error": f"old_text not found in {path}"}
    if content.count(old_text) > 1:
        return {"error": f"old_text found {content.count(old_text)} times in {path}, must be unique"}
    content = content.replace(old_text, new_text)
    full.write_text(content)
    return {"ok": True, "path": path}


def _search(target_path, pattern, include=None):
    cmd = ["grep", "-rn", "-E", pattern]
    if include:
        cmd.extend(["--include", include])
    cmd.append(target_path)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    lines = r.stdout.strip().split("\n")[:100]
    results = []
    for line in lines:
        if ":" in line:
            parts = line.split(":", 2)
            if len(parts) >= 3:
                results.append({"file": parts[0], "line": parts[1], "text": parts[2][:200]})
    return {"matches": len(results), "results": results[:50]}


def _list_files(target_path, path=""):
    full = Path(target_path) / path
    if not full.is_dir():
        return {"error": f"Not a directory: {path}"}
    entries = []
    for p in sorted(full.iterdir())[:200]:
        rel = p.relative_to(target_path)
        entries.append({"name": rel.as_posix(), "is_dir": p.is_dir()})
    return {"entries": entries}


def register_tools(agent, target_path: str):
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
        func=lambda command, timeout=120: _bash(target_path, command, timeout),
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
        func=lambda path: _read_file(target_path, path),
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
        func=lambda path, content: _write_file(target_path, path, content),
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
        func=lambda path, old_text, new_text: _edit_file(target_path, path, old_text, new_text),
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
        func=lambda pattern, include=None: _search(target_path, pattern, include),
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
        func=lambda path="": _list_files(target_path, path),
    )
