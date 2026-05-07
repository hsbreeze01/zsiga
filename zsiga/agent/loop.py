import json
import subprocess
from pathlib import Path
from zai import ZaiClient


class AgentLoop:

    def __init__(self, api_key: str, model: str = "glm-4.7"):
        self.client = ZaiClient(api_key=api_key)
        self.model = model
        self.tools = []
        self.tool_funcs = {}
        self.max_turns = 40

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
                  max_turns: int = None) -> str:
        max_turns = max_turns or self.max_turns
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for _ in range(max_turns):
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
                    result = await self.tool_funcs[name](**args)
                    result_str = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})

                messages.append({
                    "role": "tool",
                    "content": result_str,
                    "tool_call_id": tc.id,
                })

        return "MAX_TURNS_REACHED"
