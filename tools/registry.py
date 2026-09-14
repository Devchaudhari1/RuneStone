from tools.filesystem import (
    read_file,
    list_directory,
    search_files,
    write_file,
)


TOOLS = {
    "read_file": read_file,
    "list_directory": list_directory,
    "search_files": search_files,
    "write_file": write_file,
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