import json
from zai import ZaiClient


def estimate_chars(messages: list) -> int:
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    total += len(part.get("text", ""))
    return total


def compact_messages(
    messages: list,
    threshold: int,
    keep_recent: int = 3,
    client: ZaiClient = None,
    model: str = "glm-5.1",
) -> tuple[list, int]:
    if estimate_chars(messages) <= threshold:
        return messages, 0

    if len(messages) <= keep_recent + 1:
        return messages, 0

    system_msg = messages[0] if messages[0].get("role") == "system" else None
    to_compress = messages[1:-keep_recent] if system_msg else messages[:-keep_recent]
    recent = messages[-keep_recent:]

    if not to_compress:
        return messages, 0

    summary_text = _generate_summary(to_compress, client, model)
    summary_msg = {
        "role": "assistant",
        "content": (
            "[compacted summary of previous work]\n"
            f"{summary_text}"
        ),
    }

    result = []
    if system_msg:
        result.append(system_msg)
    result.append(summary_msg)
    result.extend(recent)

    return result, 1


def _generate_summary(messages: list, client: ZaiClient, model: str) -> str:
    if client is None:
        return _fallback_summary(messages)

    history_lines = []
    for m in messages:
        role = m.get("role", "unknown")
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                p.get("text", "") for p in content if isinstance(p, dict)
            )
        if isinstance(content, str) and len(content) > 500:
            content = content[:500] + "..."
        history_lines.append(f"[{role}] {content}")

    history_text = "\n".join(history_lines)
    if len(history_text) > 15000:
        history_text = history_text[:15000] + "\n... (truncated)"

    prompt = (
        "Summarize the following agent work history in 3-5 bullet points. "
        "Focus on: what was done, what decisions were made, what files were modified, "
        "current progress (which tasks completed, which remain). "
        "Be concise and factual.\n\n"
        f"{history_text}"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1,
        )
        return resp.choices[0].message.content or _fallback_summary(messages)
    except Exception:
        return _fallback_summary(messages)


def _fallback_summary(messages: list) -> str:
    tool_calls = 0
    files_read = set()
    files_written = set()
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "assistant":
            tcs = m.get("tool_calls", [])
            tool_calls += len(tcs)
            for tc in tcs:
                args = tc.get("function", {}).get("arguments", "")
                try:
                    parsed = json.loads(args)
                    if "path" in parsed:
                        files_read.add(parsed["path"])
                    if "command" in parsed:
                        cmd = parsed["command"]
                        if "cat >" in cmd or "write" in cmd:
                            for part in cmd.split():
                                if "/" in part and part.endswith((".py", ".md", ".html")):
                                    files_written.add(part)
                except (json.JSONDecodeError, TypeError):
                    pass
    parts = [f"Compressed {len(messages)} messages ({tool_calls} tool calls)."]
    if files_read:
        parts.append(f"Files touched: {', '.join(sorted(files_read)[:10])}")
    return "\n".join(parts)
