import inspect
import json
import logging
import re
import time
from zai import ZaiClient
from zsiga.agent.compaction import compact_messages, estimate_tokens
from zsiga.agent.token_budget import TokenBudget
from zsiga.agent.value_signal import ValueTracker, classify_turn

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fallback tool-call extractor for non-JSON LLM outputs
# ---------------------------------------------------------------------------

def _extract_tool_calls_from_content(content: str) -> list[tuple[str, dict]]:
    """Parse pseudo tool calls from LLM text when the API returns none.

    Handles three formats that glm-5.1 has been observed to emit:

    1. XML  ``<tool_call name="X"><arg name="Y">val</arg></tool_call_list>``
    2. XML  ``<invoke name="X"><parameter name="Y">val</parameter></invoke>``
    3. Inline JSON  ``{"name": "X", "arguments": {"Y": "val"}}``

    Returns a list of ``(tool_name, args_dict)`` tuples.  Only includes tools
    whose *tool_name* matches a known tool in ``allowed_tools`` (caller must
    filter).
    """
    if not content:
        return []

    calls: list[tuple[str, dict]] = []

    # --- XML format 1: <tool_call name="..."><arg name="...">val</arg> ---
    for m in re.finditer(
        r'<tool_call\s+name=["\'](\w+)["\']\s*>(.*?)</tool_call',
        content, re.DOTALL | re.IGNORECASE,
    ):
        name = m.group(1)
        args: dict = {}
        for arg_m in re.finditer(
            r'<arg\s+name=["\']([^"\']+)["\']\s*>(.*?)</arg>',
            m.group(2), re.DOTALL,
        ):
            val = arg_m.group(2).strip()
            # Try JSON decode for non-string values
            try:
                val = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                pass
            args[arg_m.group(1)] = val
        calls.append((name, args))

    # --- XML format 2: <invoke name="..."><parameter name="...">val</parameter> ---
    if not calls:
        for m in re.finditer(
            r'<invoke\s+name=["\'](\w+)["\']\s*>(.*?)</invoke',
            content, re.DOTALL | re.IGNORECASE,
        ):
            name = m.group(1)
            args = {}
            for param_m in re.finditer(
                r'<parameter\s+name=["\']([^"\']+)["\']\s*>(.*?)</parameter>',
                m.group(2), re.DOTALL,
            ):
                val = param_m.group(2).strip()
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    pass
                args[param_m.group(1)] = val
            calls.append((name, args))

    # --- Inline JSON: {"name": "...", "arguments": {...}} ---
    if not calls:
        for m in re.finditer(
            r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}',
            content,
        ):
            name = m.group(1)
            try:
                args = json.loads(m.group(2))
                calls.append((name, args))
            except json.JSONDecodeError:
                pass

    return calls


def _build_llm_client(provider: str, api_key: str, base_url: str | None,
                     proxy: str | None):
    """Return an OpenAI-compatible client for the requested *provider*.

    Both ZaiClient (zhipuai) and openai.OpenAI expose
    ``client.chat.completions.create(...)`` with the same return shape, so
    the rest of AgentLoop is provider-agnostic.
    """
    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    if proxy:
        import httpx
        kwargs["http_client"] = httpx.Client(proxy=proxy, timeout=120.0)
    if provider == "openai":
        from openai import OpenAI
        return OpenAI(**kwargs)
    return ZaiClient(**kwargs)

log = logging.getLogger(__name__)


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
                 compaction_threshold: int = 30000,
                 compaction_keep_recent: int = 4,
                 total_budget: int = 1200000,
                 per_turn_limit: int = 8192,
                 compaction_ratio: float = 0.8,
                 stale_limit: int = 10,
                 budget_extend_factor: float = 1.5,
                 provider: str = "zhipuai",
                 max_tokens: int = 4096):
        self.provider = provider
        self.client = _build_llm_client(provider, api_key, base_url, proxy)
        self.model = model
        self._max_tokens = max_tokens
        self.tools = []
        self.tool_funcs = {}
        self.max_turns = 40
        self.context = ""
        self._phase_label = ""
        self.compaction_enabled = compaction_enabled
        self.compaction_threshold = compaction_threshold
        self.compaction_keep_recent = compaction_keep_recent
        self.budget = TokenBudget(
            total_budget=total_budget,
            per_turn_limit=per_turn_limit,
            compaction_threshold=compaction_threshold,
            compaction_ratio=compaction_ratio,
            stale_limit=stale_limit,
            budget_extend_factor=budget_extend_factor,
        )
        self.value_tracker = ValueTracker(stale_limit=stale_limit)
        self._default_stale_limit = stale_limit

    def set_phase(self, label: str):
        self._phase_label = label
        self.budget._used = 0
        self.budget._extended = False
        self.budget._consecutive_stale = 0
        self.value_tracker.reset()

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

        log.info("starting (max=%d turns, timeout=%ss)",
                 max_turns, timeout_seconds or '∞',
                 extra={"phase": phase, "max_turns": max_turns,
                        "timeout_seconds": timeout_seconds})

        for turn in range(max_turns):
            elapsed = time.monotonic() - start
            if timeout_seconds and elapsed > timeout_seconds:
                log.warning("⏱️ TIMEOUT after %d turns, %.1fs, %d LLM calls, %d tool calls",
                            turn, elapsed, llm_calls_total, tool_calls_total,
                            extra={"phase": phase, "turn": turn,
                                   "elapsed_seconds": round(elapsed, 1),
                                   "llm_calls": llm_calls_total,
                                   "tool_calls": tool_calls_total})
                return RunResult("TIMEOUT", llm_calls_total, tool_calls_total, elapsed,
                                 prompt_tokens_total, completion_tokens_total)

            t_llm = time.monotonic()

            if self.compaction_enabled and turn > 0 and self.budget.should_compact(messages, estimate_tokens):
                messages, compacted = compact_messages(
                    messages,
                    threshold=self.compaction_threshold,
                    keep_recent=self.compaction_keep_recent,
                    client=self.client,
                    model=self.model,
                )
                if compacted:
                    new_tokens = estimate_tokens(messages)
                    log.debug("🗜️ compacted → %d msgs, %d tokens",
                              len(messages), new_tokens,
                              extra={"phase": phase})

            # Wrap LLM call with hard timeout to prevent API hangs
            _llm_timeout = 300  # 5 min hard timeout per LLM call
            try:
                import asyncio
                _running_loop = asyncio.get_running_loop()
                resp = await asyncio.wait_for(
                    _running_loop.run_in_executor(
                        None,
                        lambda: self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            tools=self.tools or None,
                            tool_choice="auto",
                            max_tokens=self._max_tokens,
                        )
                    ),
                    timeout=_llm_timeout,
                )
            except asyncio.TimeoutError:
                elapsed = time.monotonic() - start
                log.warning("LLM API timeout after %ds, aborting run", _llm_timeout)
                return RunResult("TIMEOUT", llm_calls_total, tool_calls_total, elapsed,
                                 prompt_tokens_total, completion_tokens_total)
            llm_calls_total += 1
            if resp.usage:
                prompt_tokens_total += getattr(resp.usage, "prompt_tokens", 0) or 0
                completion_tokens_total += getattr(resp.usage, "completion_tokens", 0) or 0
            _ = (time.monotonic() - t_llm) * 1000

            try:
                from .langfuse_shim import llm_generation
                _msg = resp.choices[0].message if resp.choices else None
                with llm_generation(f"turn-{llm_calls_total}", model=self.model) as _gen:
                    if _gen is not None:
                        _gen.update(
                            input=str(messages[-1])[:2000] if messages else None,
                            output=_msg.content[:2000] if _msg and _msg.content else None,
                            usage_details={
                                "input": getattr(resp.usage, "prompt_tokens", 0) or 0,
                                "output": getattr(resp.usage, "completion_tokens", 0) or 0,
                                "total": (getattr(resp.usage, "prompt_tokens", 0) or 0)
                                         + (getattr(resp.usage, "completion_tokens", 0) or 0),
                            },
                        )
            except Exception:
                pass

            # Budget enforcement after recording token usage
            if resp.usage:
                budget_status = self.budget.record(
                    getattr(resp.usage, "prompt_tokens", 0) or 0,
                    getattr(resp.usage, "completion_tokens", 0) or 0,
                )
                if budget_status["turn_exceeded"]:
                    log.warning(
                        "⚠️ turn_exceeded: completion_tokens=%d > per_turn_limit=%d "
                        "(turn %d, phase=%s) — continuing",
                        getattr(resp.usage, "completion_tokens", 0) or 0,
                        self.budget.per_turn_limit,
                        turn + 1, phase,
                    )
                if budget_status["session_exceeded"]:
                    extended = self.budget.try_extend("productive")
                    if not extended:
                        elapsed = time.monotonic() - start
                        log.warning(
                            "🚫 BUDGET_EXCEEDED after turn %d | used=%d remaining=%d",
                            turn + 1, budget_status["used"], budget_status["remaining"],
                            extra={"phase": phase, "turn": turn + 1, **budget_status},
                        )
                        return RunResult(
                            "BUDGET_EXCEEDED", llm_calls_total, tool_calls_total, elapsed,
                            prompt_tokens_total, completion_tokens_total,
                        )
            msg = resp.choices[0].message
            messages.append(msg.model_dump())

            if not msg.tool_calls:
                # Fallback: try to extract tool calls from XML/JSON in content
                extracted = _extract_tool_calls_from_content(msg.content or "")
                valid_extracted = [(n, a) for n, a in extracted if n in self.tool_funcs]
                if valid_extracted:
                    log.warning(
                        "⚠️ fallback tool-call parser: %d calls extracted from content "
                        "(LLM did not return proper tool_calls JSON)",
                        len(valid_extracted),
                        extra={"phase": phase, "tools": [n for n, _ in valid_extracted]},
                    )
                    tool_calls_total += len(valid_extracted)
                    turn_tool_names: list[str] = []
                    turn_tool_results: list[dict] = []
                    for tc_name, tc_args in valid_extracted:
                        t_tool = time.monotonic()
                        try:
                            result = self.tool_funcs[tc_name](**tc_args)
                            if inspect.isawaitable(result):
                                result = await result
                            result_str = json.dumps(result, ensure_ascii=False, default=str)
                        except Exception as e:
                            result_str = json.dumps({"error": str(e)})
                            result = {"error": str(e)}
                        tool_ms = (time.monotonic() - t_tool) * 1000
                        log.debug("    → fallback %.0fms, %d chars", tool_ms, len(result_str),
                                  extra={"phase": phase, "tool_name": tc_name})
                        turn_tool_names.append(tc_name)
                        turn_tool_results.append(result if isinstance(result, dict) else {})
                        messages.append({
                            "role": "tool",
                            "content": result_str,
                            "name": tc_name,
                        })
                    # continue to next turn instead of returning
                    continue

                elapsed = time.monotonic() - start
                content_preview = (msg.content or "")[:80].replace("\n", " ")
                log.info("✅ done in %.1fs | %d LLM calls, %d tool calls | response: %s...",
                         elapsed, llm_calls_total, tool_calls_total, content_preview,
                         extra={"phase": phase, "elapsed_seconds": round(elapsed, 1),
                                "llm_calls": llm_calls_total, "tool_calls": tool_calls_total})
                return RunResult(msg.content, llm_calls_total, tool_calls_total, elapsed,
                                 prompt_tokens_total, completion_tokens_total)

            turn_tools = len(msg.tool_calls)
            tool_calls_total += turn_tools

            # Collect tool names and results for value-signal classification
            turn_tool_names: list[str] = []
            turn_tool_results: list[dict] = []

            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                args_preview = json.dumps(args, ensure_ascii=False)[:120]
                log.debug("turn %d: 🔧 %s(%s)", turn + 1, name, args_preview,
                          extra={"phase": phase, "turn": turn + 1,
                                 "tool_name": name, "args_preview": args_preview})

                t_tool = time.monotonic()
                try:
                    result = self.tool_funcs[name](**args)
                    if inspect.isawaitable(result):
                        result = await result
                    result_str = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
                    result = {"error": str(e)}
                tool_ms = (time.monotonic() - t_tool) * 1000

                turn_tool_names.append(name)
                turn_tool_results.append(result if isinstance(result, dict) else {})

                result_len = len(result_str)
                log.debug("    → %.0fms, %d chars", tool_ms, result_len,
                          extra={"phase": phase, "tool_name": name,
                                 "tool_ms": round(tool_ms)})

                messages.append({
                    "role": "tool",
                    "content": result_str,
                    "tool_call_id": tc.id,
                })

            # Value-signal classification after tool calls complete
            turn_signal = classify_turn(turn_tool_names, turn_tool_results)
            tracker_status = self.value_tracker.record_turn(turn_signal)

            # Re-record budget with value_signal for stale tracking
            if resp.usage:
                budget_status = self.budget.record(
                    0, 0,
                    value_signal=turn_signal,
                )

            # Stale-limit check (primary stop)
            if tracker_status["limit_reached"]:
                elapsed = time.monotonic() - start
                log.warning(
                    "🛑 STALE_LIMIT after turn %d | stale_count=%d",
                    turn + 1, tracker_status["stale_count"],
                    extra={"phase": phase, "turn": turn + 1, **tracker_status},
                )
                return RunResult(
                    "STALE_LIMIT", llm_calls_total, tool_calls_total, elapsed,
                    prompt_tokens_total, completion_tokens_total,
                )

        elapsed = time.monotonic() - start
        log.warning("⚠️ MAX_TURNS (%d) reached after %.1fs, %d tool calls",
                    max_turns, elapsed, tool_calls_total,
                    extra={"phase": phase, "max_turns": max_turns,
                           "elapsed_seconds": round(elapsed, 1),
                           "tool_calls": tool_calls_total})
        return RunResult("MAX_TURNS_REACHED", llm_calls_total, tool_calls_total, elapsed,
                         prompt_tokens_total, completion_tokens_total)
