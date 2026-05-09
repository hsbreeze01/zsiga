import asyncio
import inspect
import json
import time
import subprocess
from pathlib import Path
from zai import ZaiClient
from zsiga.agent.compaction import compact_messages, estimate_chars


class RunResult:
    __slots__ = ("content", "llm_calls", "tool_calls", "elapsed_seconds",
                 "prompt_tokens", "completion_tokens")

    def __init__(self, content: str, llm_calls: int, tool_calls: int,
                 elapsed_seconds: float, prompt_tokens: int = 0,
                 completion_tokens: int = 0):
        self.content = content
        self.llm_calls = llm_calls
        self.tool_calls = tool_calls
        self.elapsed_seconds = elapsed_seconds
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    def __str__(self):
        return self.content


class AgentLoop:

    def __init__(self, api_key: str, model: str = "glm-5.1",
                 base_url: str = None, proxy: str = None,
                 compaction_enabled: bool = True,
                 compaction_threshold: int = 60000,
                 compaction_keep_recent: int = 3):
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        if proxy:
            import httpx
            kwargs["http_client"] = httpx.Client(
                proxy=proxy, timeout=120.0,
            )
        self.client = ZaiClient(**kwargs)
        self.model = model
        self.tools = []
        self.tool_funcs = {}
        self.max_turns = 40
        self.context = ""
        self._phase_label = ""
        self.compaction_enabled = compaction_enabled
        self.compaction_threshold = compaction_threshold
        self.compaction_keep_recent = compaction_keep_recent

    def set_phase(self, label: str):
        self._phase_label = label

    def register_tool(self, name, description, parameters, func):
        self.tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        })
        self.tool_funcs[name] = func

    async def run(self, system_prompt: str, user_prompt: str,
                   max_turns: int = None, timeout_seconds: int = None) -> RunResult:
        max_turns = max_turns or self.max_turns
        if self.context:
            system_prompt = f"{self.context}\n\n---\n\n{system_prompt}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        phase = self._phase_label or "agent"
        start = time.monotonic()
        tool_calls_total = 0
        llm_calls_total = 0
        prompt_tokens_total = 0
        completion_tokens_total = 0

        print(f"  [{phase}] starting (max={max_turns} turns, timeout={timeout_seconds or '∞'}s)")

        for turn in range(max_turns):
            elapsed = time.monotonic() - start
            if timeout_seconds and elapsed > timeout_seconds:
                print(f"  [{phase}] ⏱️ TIMEOUT after {turn} turns, {elapsed:.1f}s, {llm_calls_total} LLM calls, {tool_calls_total} tool calls")
                return RunResult("TIMEOUT", llm_calls_total, tool_calls_total, elapsed,
                                 prompt_tokens_total, completion_tokens_total)

            t_llm = time.monotonic()

            if self.compaction_enabled and turn > 0 and turn % 3 == 0:
                messages, compacted = compact_messages(
                    messages,
                    threshold=self.compaction_threshold,
                    keep_recent=self.compaction_keep_recent,
                    client=self.client,
                    model=self.model,
                )
                if compacted:
                    new_chars = estimate_chars(messages)
                    print(f"  [{phase}] 🗜️ compacted → {len(messages)} msgs, {new_chars} chars")

            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools or None,
                tool_choice="auto",
            )
            llm_calls_total += 1
            if resp.usage:
                prompt_tokens_total += getattr(resp.usage, "prompt_tokens", 0) or 0
                completion_tokens_total += getattr(resp.usage, "completion_tokens", 0) or 0
            llm_ms = (time.monotonic() - t_llm) * 1000
            msg = resp.choices[0].message
            messages.append(msg.model_dump())

            if not msg.tool_calls:
                elapsed = time.monotonic() - start
                content_preview = (msg.content or "")[:80].replace("\n", " ")
                print(f"  [{phase}] ✅ done in {elapsed:.1f}s | {llm_calls_total} LLM calls, {tool_calls_total} tool calls | response: {content_preview}...")
                return RunResult(msg.content, llm_calls_total, tool_calls_total, elapsed,
                                 prompt_tokens_total, completion_tokens_total)

            turn_tools = len(msg.tool_calls)
            tool_calls_total += turn_tools

            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                args_preview = json.dumps(args, ensure_ascii=False)[:120]
                print(f"  [{phase}] turn {turn+1}: 🔧 {name}({args_preview})")

                t_tool = time.monotonic()
                try:
                    result = self.tool_funcs[name](**args)
                    if inspect.isawaitable(result):
                        result = await result
                    result_str = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
                tool_ms = (time.monotonic() - t_tool) * 1000

                result_lines = result_str.count("\n") + 1
                result_len = len(result_str)
                print(f"  [{phase}]     → {tool_ms:.0f}ms, {result_len} chars")

                messages.append({
                    "role": "tool",
                    "content": result_str,
                    "tool_call_id": tc.id,
                })

        elapsed = time.monotonic() - start
        print(f"  [{phase}] ⚠️ MAX_TURNS ({max_turns}) reached after {elapsed:.1f}s, {tool_calls_total} tool calls")
        return RunResult("MAX_TURNS_REACHED", llm_calls_total, tool_calls_total, elapsed,
                         prompt_tokens_total, completion_tokens_total)
