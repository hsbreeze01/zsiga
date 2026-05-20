import inspect
import json
import logging
import time
from zai import ZaiClient
from zsiga.agent.compaction import compact_messages, estimate_tokens
from zsiga.agent.token_budget import TokenBudget
from zsiga.agent.value_signal import ValueTracker, classify_turn

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
                 compaction_threshold: int = 60000,
                 compaction_keep_recent: int = 3,
                 total_budget: int = 1200000,
                 per_turn_limit: int = 8192,
                 compaction_ratio: float = 0.8,
                 stale_limit: int = 10,
                 budget_extend_factor: float = 1.5):
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
                resp = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            tools=self.tools or None,
                            tool_choice="auto",
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

            # Budget enforcement after recording token usage
            if resp.usage:
                budget_status = self.budget.record(
                    getattr(resp.usage, "prompt_tokens", 0) or 0,
                    getattr(resp.usage, "completion_tokens", 0) or 0,
                )
                if budget_status["session_exceeded"] or budget_status["turn_exceeded"]:
                    # Soft budget extension: if last turn was productive, try extending
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
