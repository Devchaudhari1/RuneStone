TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories inside a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path. Defaults to the current directory.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search recursively through text files for a string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory to search.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to search for.",
                    },
                },
                "required": ["path", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Complete text content to write.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command inside the Rune Stone workspace. "
                "Use this to run tests, inspect the project, or execute "
                "development commands. The working directory must be inside "
                "the workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute.",
                    },
                    "working_directory": {
                        "type": "string",
                        "description": (
                            "Directory where the command should run. "
                            "Defaults to the current directory."
                        ),
                    },
                    "timeout": {
                        "type": "integer",
                        "description": (
                            "Maximum execution time in seconds. "
                            "Defaults to 30."
                        ),
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": (
                "Search the structural code index of the workspace "
                "repository. Use this to find functions, classes, "
                "methods, imports, and relevant source code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Symbol name, class name, function name, "
                            "file name, or code text to search for."
                        ),
                    },
                    "repository": {
                        "type": "string",
                        "description": (
                            "Repository path relative to the workspace. "
                            "Defaults to the current repository."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_semantic",
            "description": (
                "Search the repository using semantic similarity. "
                "Use this when you know what kind of code or behavior "
                "you are looking for but do not know the exact symbol name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural-language description of the code, "
                            "behavior, feature, or logic to find."
                        ),
                    },
                    "repository": {
                        "type": "string",
                        "description": (
                            "Repository path relative to the workspace. "
                            "Defaults to the current repository."
                        ),
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of results to return.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Make a minimal edit to an existing file. "
                "If old_text occurs exactly once, a source range is not required. "
                "If old_text occurs multiple times, provide the exact source range. "
                "When using a range, lines are 1-based, columns are 0-based, "
                "and the end position is exclusive. "
                "The text at the range must exactly match old_text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file inside the workspace."
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Exact text that should currently exist."
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Replacement text."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "1-based starting line. Optional."
                    },
                    "start_column": {
                        "type": "integer",
                        "description": "0-based starting column. Optional."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "1-based ending line. Optional."
                    },
                    "end_column": {
                        "type": "integer",
                        "description": "0-based exclusive ending column. Optional."
                    }
                },
                "required": [
                    "path",
                    "old_text",
                    "new_text"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "Search the local knowledge base for relevant documentation, "
                "notes, and other indexed knowledge. Use this when the answer "
                "may be contained in project documentation rather than source code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language search query.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of results to return.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ingest_knowledge",
            "description": (
                "Download a remote HTTPS document and add it "
                "to the RuneStone external knowledge base."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "HTTPS URL of the document to ingest."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "refresh_knowledge",
            "description": (
                "Re-download an existing external knowledge source."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_knowledge",
            "description": (
                "Remove an external knowledge source from "
                "the RuneStone knowledge base."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": ["url"]
            }
        }
    }
]