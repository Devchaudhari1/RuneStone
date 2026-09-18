from tools.filesystem import (
    read_file,
    list_directory,
    search_files,
    write_file,
    edit_file,
)

from tools.terminal import run_command
from tools.code_index import search_code
from tools.semantic_search import search_semantic
from tools.knowledge_search import search_knowledge

from tools.knowledge_ingest import (
    ingest_knowledge,
    refresh_knowledge,
    remove_knowledge,
)

TOOLS = {
    "read_file": read_file,
    "list_directory": list_directory,
    "search_files": search_files,
    "write_file": write_file,
    "edit_file": edit_file,
    "run_command": run_command,
    "search_code": search_code,
    "search_semantic": search_semantic,
    "search_knowledge": search_knowledge,
    "ingest_knowledge": ingest_knowledge,
    "refresh_knowledge": refresh_knowledge,
    "remove_knowledge": remove_knowledge,
}


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a registered tool."""

    tool = TOOLS.get(name)

    if tool is None:
        return f"Error: unknown tool: {name}"

    try:
        result = tool(**arguments)
        return str(result)

    except Exception as e:
        return f"Error executing {name}: {e}"