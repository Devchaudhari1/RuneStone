# Tools

RuneStone exposes several tools to the agent.

## Filesystem Tools

read_file reads an existing text file.

list_directory lists files and directories inside the workspace.

search_files searches workspace files for matching text.

write_file creates or replaces a file.

edit_file performs a precise modification to an existing file.

## Terminal

run_command executes a command through the Docker sandbox.

The terminal tool passes the requested workspace directory to the sandbox.

## Code Retrieval

search_code searches source code using the code index.

search_semantic performs semantic search over source code.

## Knowledge Retrieval

search_knowledge searches the RuneStone knowledge base using hybrid retrieval.

The search tool can optionally restrict results to documentation, notes, or external knowledge.