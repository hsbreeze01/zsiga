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


def _count_tool_overhead(msg: dict, overhead_per_tool_call: int = 20) -> int:
    """Return token overhead for a single message based on role and tool_calls."""
    overhead = 0
    tool_calls = msg.get("tool_calls")
    if tool_calls:
        overhead += len(tool_calls) * overhead_per_tool_call
    if msg.get("role") == "tool":
        overhead += overhead_per_tool_call
    return overhead


def estimate_tokens(
    messages: list,
    overhead_per_message: int = 15,
    overhead_per_tool_call: int = 20,
) -> int:
    """Estimate token count including per-message and per-tool-call overhead."""
    base = estimate_chars(messages)
    msg_overhead = len(messages) * overhead_per_message
    tool_overhead = sum(
        _count_tool_overhead(m, overhead_per_tool_call) for m in messages
    )
    return base + msg_overhead + tool_overhead


def _truncate_tool_result(msg: dict, max_chars: int) -> dict:
    """Truncate tool result content to max_chars//2 + truncation marker if over limit."""
    content = msg.get("content", "")
    if isinstance(content, str) and len(content) > max_chars:
        half = max_chars // 2
        content = f"{content[:half]}... [truncated, was {len(content)} chars]"
        msg = {**msg, "content": content}
    return msg


def _merge_tool_groups(messages: list) -> list:
    """Walk messages, identify consecutive tool-call rounds for the same tool, merge them."""
    result = []
    i = 0
    while i < len(messages):
        m = messages[i]
        if (
            m.get("role") == "assistant"
            and m.get("tool_calls")
            and len(m["tool_calls"]) == 1
        ):
            tool_name = m["tool_calls"][0].get("function", {}).get("name", "")
            if tool_name:
                group_args = []
                group_outputs = []
                group_rounds = []

                j = i
                while j < len(messages):
                    cur = messages[j]
                    if (
                        cur.get("role") == "assistant"
                        and cur.get("tool_calls")
                        and len(cur["tool_calls"]) == 1
                        and cur["tool_calls"][0].get("function", {}).get("name", "")
                        == tool_name
                    ):
                        tc = cur["tool_calls"][0]
                        args_str = tc.get("function", {}).get("arguments", "")
                        group_args.append(args_str)
                        group_rounds.append((j, cur))

                        if j + 1 < len(messages) and messages[j + 1].get("role") == "tool":
                            output = messages[j + 1].get("content", "")
                            if isinstance(output, str):
                                group_outputs.append(output[:200])
                            j += 2
                        else:
                            j += 1
                    else:
                        break

                if len(group_rounds) > 1:
                    merged_content = f"[merged {len(group_rounds)} {tool_name} calls] "
                    merged_content += "; ".join(group_args)
                    merged_output = "\n---\n".join(group_outputs)
                    if len(merged_output) > 2000:
                        merged_output = merged_output[:2000] + "... [truncated]"
                    result.append({"role": "assistant", "content": merged_content})
                    result.append({"role": "tool", "content": merged_output,
                                   "tool_call_id": "merged"})
                    i = j
                    continue
        result.append(m)
        i += 1
    return result


def _compress_patterns(messages: list, max_tool_result_chars: int = 2000) -> list:
    """Truncate long tool results, then merge consecutive same-tool call groups."""
    truncated = []
    for m in messages:
        if m.get("role") == "tool":
            truncated.append(_truncate_tool_result(m, max_tool_result_chars))
        else:
            truncated.append(m)
    return _merge_tool_groups(truncated)


def _preserve_tool_chains(
    to_compress: list, recent: list
) -> tuple[set, set]:
    """Identify tool-call chains in to_compress that are referenced by recent messages.

    Returns (preserved_assistant_indices, preserved_tool_result_indices) —
    index sets relative to to_compress.
    """
    tool_call_to_parent = {}
    for i, m in enumerate(to_compress):
        if m.get("role") == "assistant" and m.get("tool_calls"):
            for tc in m["tool_calls"]:
                tc_id = tc.get("id", "")
                if tc_id:
                    tool_call_to_parent[tc_id] = i

    recent_tool_ids = set()
    for m in recent:
        tid = m.get("tool_call_id", "")
        if tid:
            recent_tool_ids.add(tid)

    parent_indices = set()
    for tid in recent_tool_ids:
        if tid in tool_call_to_parent:
            parent_indices.add(tool_call_to_parent[tid])

    all_tool_ids_from_parents = set()
    for pi in parent_indices:
        for tc in to_compress[pi].get("tool_calls", []):
            tc_id = tc.get("id", "")
            if tc_id:
                all_tool_ids_from_parents.add(tc_id)

    tool_result_indices = set()
    for i, m in enumerate(to_compress):
        if m.get("role") == "tool" and m.get("tool_call_id", "") in all_tool_ids_from_parents:
            tool_result_indices.add(i)

    return parent_indices, tool_result_indices


def compact_messages(
    messages: list,
    threshold: int,
    keep_recent: int = 3,
    client: ZaiClient = None,
    model: str = "glm-5.1",
    *,
    max_tool_result_chars: int = 2000,
    overhead_per_message: int = 15,
    overhead_per_tool_call: int = 20,
) -> tuple[list, int]:
    if estimate_tokens(
        messages,
        overhead_per_message=overhead_per_message,
        overhead_per_tool_call=overhead_per_tool_call,
    ) <= threshold:
        return messages, 0

    if len(messages) <= keep_recent + 1:
        return messages, 0

    system_msg = messages[0] if messages[0].get("role") == "system" else None
    recent = messages[-keep_recent:]
    to_compress = messages[1:-keep_recent] if system_msg else messages[:-keep_recent]

    preserved_asst_indices, preserved_tool_indices = _preserve_tool_chains(
        to_compress, recent
    )

    preserved = []
    for i, m in enumerate(to_compress):
        if i in preserved_asst_indices or i in preserved_tool_indices:
            preserved.append(m)

    to_compress_final = [m for m in to_compress if m not in preserved]

    if not to_compress_final:
        return messages, 0

    # Phase 1: pattern compression
    compressed = _compress_patterns(
        to_compress_final, max_tool_result_chars=max_tool_result_chars
    )

    # Re-check threshold after Phase 1
    phase1_result = []
    if system_msg:
        phase1_result.append(system_msg)
    phase1_result.extend(preserved)
    phase1_result.extend(compressed)
    phase1_result.extend(recent)

    if estimate_tokens(
        phase1_result,
        overhead_per_message=overhead_per_message,
        overhead_per_tool_call=overhead_per_tool_call,
    ) <= threshold:
        return phase1_result, 1

    # Phase 2: LLM summarization of the pattern-compressed section
    summary_text = _generate_summary(compressed, client, model)
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
    result.extend(preserved)
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
    commands = set()
    error_count = 0
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "assistant":
            tcs = m.get("tool_calls", [])
            tool_calls += len(tcs)
            for tc in tcs:
                func = tc.get("function", {})
                name = func.get("name", "")
                args_str = func.get("arguments", "")
                try:
                    parsed = json.loads(args_str)
                except (json.JSONDecodeError, TypeError):
                    parsed = {}
                if name == "read_file" and "path" in parsed:
                    files_read.add(parsed["path"])
                if name == "write_file" and "path" in parsed:
                    files_written.add(parsed["path"])
                if name == "bash" and "command" in parsed:
                    commands.add(parsed["command"].strip())
        if role == "tool" and isinstance(content, str) and '"error"' in content:
            error_count += 1
    parts = [
        f"Compressed {len(messages)} messages ({tool_calls} tool calls)."
    ]
    if files_read:
        parts.append(f"Files read: {', '.join(sorted(files_read)[:10])}")
    if files_written:
        parts.append(f"Files written: {', '.join(sorted(files_written)[:10])}")
    if commands:
        unique_cmds = sorted(commands)[:10]
        parts.append(f"Shell commands: {', '.join(unique_cmds)}")
    if error_count:
        parts.append(f"Errors encountered: {error_count}")
    return "\n".join(parts)
