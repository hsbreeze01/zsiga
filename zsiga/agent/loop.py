import asyncio
import inspect
import json
import time
import subprocess
from pathlib import Path
from zai import ZaiClient


class AgentLoop:

    def __init__(self, api_key: str, model: str = "glm-5.1",
                 base_url: str = None, proxy: str = None):
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
                  max_turns: int = None, timeout_seconds: int = None) -> str:
        max_turns = max_turns or self.max_turns
        if self.context:
            system_prompt = f"{self.context}\n\n---\n\n{system_prompt}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        start = time.monotonic()
        for turn in range(max_turns):
            if timeout_seconds and (time.monotonic() - start) > timeout_seconds:
                print(f"  ⏱️ agent.run timeout after {turn} turns")
                return "TIMEOUT"

            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools or None,
                tool_choice="auto",
            )
            msg = resp.choices[0].message
            messages.append(msg.model_dump())

            if not msg.tool_calls:
                return msg.content

            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                print(f"  🔧 {name}({json.dumps(args, ensure_ascii=False)[:200]})")

                try:
                    result = self.tool_funcs[name](**args)
                    if inspect.isawaitable(result):
                        result = await result
                    result_str = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})

                messages.append({
                    "role": "tool",
                    "content": result_str,
                    "tool_call_id": tc.id,
                })

        print(f"  ⚠️ MAX_TURNS ({max_turns}) reached")
        return "MAX_TURNS_REACHED"
