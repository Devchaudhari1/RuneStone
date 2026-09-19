import json

from server.llm import LocalLLM
from tools.registry import execute_tool
from tools.schemas import TOOLS_SCHEMA

MAX_ITERATIONS = 10

COMPLETION_RULES = """
Before finishing the task:

1. Review the original user requirements.
2. Check every requirement against the actions you actually performed.
3. If multiple relevant implementations were identified, verify each one.
4. Passing tests does not automatically mean every requirement is satisfied.
5. If any requirement remains incomplete, continue working.
6. Only provide a final answer when all requirements are satisfied or
   you genuinely cannot proceed.
"""


class RuneStoneAgent:
    def __init__(self):
        self.llm = LocalLLM()
        
        self.metrics = {
            "iterations": 0,
            "tool_calls": 0,
            "tools": [],
            "files_modified": [],
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "per_iteration": [],
        }
        
    def run(self, user_message: str):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Rune Stone, a local AI agent with access to a workspace, "
                    "local knowledge, code search, and controlled web search.\n\n"

                    "You can help with software engineering tasks as well as general "
                    "information requests.\n\n"

                    "When a request requires current or external information, use the "
                    "web_search tool rather than relying on memory.\n\n"

                    "For software engineering tasks, inspect the workspace, make the "
                    "necessary changes, and validate them.\n\n"

                    "Your job is to solve software engineering tasks by:\n"
                    "1. Inspecting the project.\n"
                    "2. Searching for relevant code.\n"
                    "3. Reading relevant files.\n"
                    "4. Inspecting tests or validation code.\n"
                    "5. Determining the required changes.\n"
                    "6. Making the necessary changes.\n"
                    "7. Running tests or validation commands.\n"
                    "8. If validation fails, analyzing the failure.\n"
                    "9. Fixing the problem based on the failure.\n"
                    "10. Re-running validation until it passes or the iteration limit "
                    "is reached.\n\n"

                    "IMPORTANT:\n"
                    "- Searching is an inspection step, not the end of the task.\n"
                    "- If the user asks you to fix, repair, implement, change, or modify "
                    "code, you must continue beyond searching.\n"
                    "- Use read_file to inspect the actual file before modifying it.\n"
                    "- Use write_file to make changes.\n"
                    "- Use run_command to validate changes whenever practical.\n"
                    "- Do not claim that code was changed unless you actually used "
                    "write_file.\n"
                    "- Do not claim that tests passed unless you actually ran them.\n"
                    "- Passing tests is necessary but does not automatically mean the "
                    "task is complete.\n"
                    "- Verify every requirement from the user's request before finishing.\n"
                    "- If multiple relevant implementations are identified, inspect "
                    "and address each one.\n"
                    "- Do not assume an untested implementation is correct merely "
                    "because existing tests pass.\n"
                    "- If a relevant implementation should not be changed, explicitly "
                    "determine why before finishing.\n\n"

                    "When searching the repository:\n"
                    "- Use search_code when you know an exact symbol, class, method, "
                    "function, or code identifier.\n"
                    "- Use search_semantic when you know what behavior or functionality "
                    "you are looking for but do not know the exact symbol name.\n"
                    "- Use search_files for exact text or configuration searches.\n"
                    "- After finding relevant code, use read_file when you need broader "
                    "file context before making changes.\n\n"

                    "Knowledge source types:\n"

                    "- documentation: official/project documentation in knowledge/docs/\n"
                    "- notes: project notes in knowledge/notes/\n"
                    "- external: externally imported knowledge in knowledge/external/\n"

                    "When the user explicitly asks about project documentation, prefer\n"
                    "source_type=\"documentation\".\n"

                    "When the user explicitly asks about project notes, prefer\n"
                    "source_type=\"notes\".\n"

                    "When no source is specified, search across all knowledge sources.\n"

                    "Do not use a source filter unless the user's request gives a reason\n"
                    "to restrict the search.\n\n"
                    "External knowledge ingestion:\n\n"

                    "- Use ingest_knowledge when the user explicitly asks RuneStone to import\n"
                    "information from a remote HTTPS URL.\n"
                    "- Use refresh_knowledge when the user asks to update an already imported\n"
                    "external source.\n"
                    "- Use remove_knowledge when the user asks to remove an imported source.\n"
                    "- Do not use run_command with curl, wget, or similar commands to fetch\n"
                    "remote knowledge.\n"
                    "- External ingestion is intentionally handled by the controlled\n"
                    "knowledge-ingestion tool.\n"
                    "- After ingestion, use search_knowledge to retrieve information from the\n"
                    "imported source when needed.\n\n"
                    
                    "WEB SEARCH:\n"
                    "- web_search is the approved tool for accessing current external web information.\n"
                    "- Use web_search for current, recent, latest, today's, yesterday's, or otherwise time-sensitive information.\n"
                    "- Use web_search for external facts that are not available in the local RuneStone knowledge base.\n"
                    "- If the user asks about something that may have changed since your training data, use web_search before answering.\n"
                    "- If the user asks for current information, do not answer from memory alone.\n"
                    "- For questions containing words such as today, current, latest, recent, newest, now, this week, or this month, strongly prefer web_search.\n"
                    "- Do not use run_command with curl, wget, Invoke-WebRequest, requests, browsers, or other commands to access the Internet.\n"
                    "- web_search is the only approved general-purpose Internet search mechanism.\n"
                    "- After receiving web_search results, use those results as evidence when forming the answer.\n"
                    "- Do not automatically save web search results into the local knowledge base.\n"
                    "- Only use ingest_knowledge when the user explicitly asks to save or import a web source.\n"
                    "- Do not claim that you searched the web unless you actually called web_search.\n"

                    "Use write_file primarily when creating a new file or when replacing an\n"
                    "entire file is explicitly necessary.\n\n"
                    "COMPLETION RULES:\n"
                    
                    "Before declaring the task complete:\n"
                    "1. Review the original user requirements.\n"
                    "2. Check every requirement against the actions you actually "
                    "performed.\n"
                    "3. Verify that every relevant implementation identified during "
                    "inspection has been addressed.\n"
                    "4. Passing tests alone is not sufficient.\n"
                    "5. If any requirement remains incomplete, continue working.\n"
                    "6. Only provide a final answer when all requirements are satisfied "
                    "or you genuinely cannot proceed.\n\n"

                    "Use tools whenever you need information or need to modify the "
                    "project.\n"
                    "Do not claim to have performed an action unless you actually used "
                    "the tool.\n"
                    "Do not stop merely because a test failed. Investigate the failure "
                    "and attempt to fix it.\n"
                    "After making a change, validate it whenever practical.\n"
                    "Be concise and technically accurate."
                ),            
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        for iteration in range(1, MAX_ITERATIONS + 1):
            print(f"\n========== Agent Iteration {iteration} ==========")

            message_chars = sum(
                len(str(message.get("content", "")))
                for message in messages
            )

            print(
                f"[Context] messages={len(messages)} "
                f"chars={message_chars:,}"
            )

            response = self.llm.chat(
                messages=messages,
                tools=TOOLS_SCHEMA,
                temperature=0.2,
                max_tokens=512,
            )
            self.metrics["iterations"] = iteration

            if response.usage:
                prompt_tokens = response.usage.prompt_tokens or 0
                completion_tokens = response.usage.completion_tokens or 0
                total_tokens = response.usage.total_tokens or 0

                self.metrics["prompt_tokens"] += prompt_tokens
                self.metrics["completion_tokens"] += completion_tokens
                self.metrics["total_tokens"] += total_tokens

                self.metrics["per_iteration"].append(
                    {
                        "iteration": iteration,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    }
                )

                print(
                    f"[Tokens] prompt={prompt_tokens} "
                    f"completion={completion_tokens} "
                    f"total={total_tokens}"
                )

            message = response.choices[0].message

            # Model finished without requesting another tool.
            if not message.tool_calls:
                return message.content or ""

            # Add assistant tool-call message to conversation.
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

            # Execute requested tools.
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                self.metrics["tool_calls"] += 1
                self.metrics["tools"].append(tool_name)
                raw_arguments = tool_call.function.arguments

                if tool_name == "write_file":
                    try:
                        arguments = json.loads(raw_arguments)
                        path = arguments.get("path")
                        if path and path not in self.metrics["files_modified"]:
                            self.metrics["files_modified"].append(path)
                    except json.JSONDecodeError:
                        pass

                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    result = "Error: invalid JSON arguments."
                    arguments = {}

                else:
                    print(f"\n[Tool] {tool_name}")
                    print(f"[Arguments] {arguments}")

                    result = execute_tool(
                        tool_name,
                        arguments,
                    )

                    print(f"[Result]\n{result[:2000]}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        return (
            f"Rune Stone stopped after reaching the maximum "
            f"of {MAX_ITERATIONS} agent iterations."
        )
    