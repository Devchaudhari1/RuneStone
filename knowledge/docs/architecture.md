# RuneStone Architecture

RuneStone is a local AI coding and computer agent.

The main agent receives a user request, reasons about the task, and can call tools to inspect files, edit code, search repositories, retrieve knowledge, and execute commands.

The local Qwen3-4B model provides the language-model reasoning layer.

## Agent and Tools

The agent communicates with tools through a tool registry.

Filesystem operations, terminal execution, code search, semantic search, and knowledge retrieval are exposed as registered tools.

## Local Inference

RuneStone uses a local Qwen3-4B model served through an OpenAI-compatible llama.cpp server.

The inference server runs on localhost and exposes the API on port 8080.