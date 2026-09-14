# Rune Stone

## Overview
    Rune Stone is a lightweight locally deployable code assistant built over hugging face's **Qwen3-4B** model. It uses **llama.cpp's GGUF** format to provide fast performance on local systems
## Installation

    The Dependencies can be installed by running the following command in terminal: 
```
    pip install -r requirements.txt
```

```
---/root
    ---/models
        ---/Qwen3-4B-GGUF
            ---/Qwen3-4B-Q5_K_M.gguf
    ---/server
        ---/__init__.py
        ---/llm.py
        ---/test_client.py
    ---tools/
        ---/__init__.py
        ---/filesystem.py
        ---/registry.py
        ---/schemas.py
        ---/terminal.py
    ---agent.py
    ---main.py
    ---test_agent.py


```