import json

from server.llm import LocalLLM
from tools.registry import execute_tool
from tools.schemas import TOOLS_SCHEMA


class RuneStoneAgent:

    def __init__(self):
        self.llm = LocalLLM()

    def run(self, user_message: str):

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Rune Stone, a local AI software engineering agent.\n"
                    "You can inspect and modify the user's codebase using tools.\n"
                    "Use tools when necessary.\n"
                    "Do not claim to have performed an action unless you actually "
                    "used the appropriate tool.\n"
                    "Be concise and technically accurate."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        while True:

            response = self.llm.chat(
                messages=messages,
                tools=TOOLS_SCHEMA,
                temperature=0.2,
                max_tokens=512,
            )

            message = response.choices[0].message

            # No tool call → final answer
            if not message.tool_calls:
                return message.content or ""

            # Add assistant's tool-call message
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in message.tool_calls
                    ],
                }
            )

            # Execute every requested tool
            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )
                except json.JSONDecodeError:
                    result = "Error: invalid JSON arguments."
                else:
                    print(
                        f"\n[Tool] {tool_name}"
                        f"\n[Arguments] {arguments}"
                    )

                    result = execute_tool(
                        tool_name,
                        arguments,
                    )

                    print(f"[Result]\n{result[:1000]}")

                # Give tool result back to model
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )