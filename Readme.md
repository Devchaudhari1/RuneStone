# Rune Stone

## Overview
    Rune Stone is a lightweight locally deployable code assistant built over hugging face's **Qwen3-4B** model. It uses **llama.cpp's GGUF** format to provide fast performance on local systems
## Installation
### Python dependencies
    The python dependencies can be installed by running the following command in terminal: 

```
    pip install -r requirements.txt
```
### Hugging face models

    Hugging face models like **Qwen3-4B-Q5_K_M.gguf** is needed to be installed and added into models/Qwen3-4B-GGUF directory. 

    Qwen can be installed using the following link:
    - https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q5_K_M.gguf?download=true

### llama.cpp
    llama.cpp can be installed using :

- Windows
    ```
        winget install llama.cpp
    ```
- macOS
    ``` 
        brew install llama.cpp
    ```

### Docker
    Rune Stone requires **Docker** to support sandboxing.

### Verify llama.cpp and Qwen installation with:

```
llama-server `
  -m ".\models\Qwen3-4B-GGUF\Qwen3-4B-Q5_K_M.gguf" `
  --alias "qwen3-4b" `
  -ngl 99 `
  --jinja `
  --reasoning off `
  --host 127.0.0.1 `
  --port 8080 `
  -c 8192
  ```

## Directory:
```
---root/
    ---benchmarks/
        ---rag/
            ---dataset.json 
            ---runner.py
        ---tasks/
            ---task001.../
            ---task002.../
            ...
        ---runner.py // runs tasks to benchmark Rune Stone
    ---embeddings/
        ---embedder.py // applies BAAI BGE embedding
    ---indexer/
        ---chunker.py // converts parsed symbols into chunks for retrieval
        ---code_index.py // indexes symbols into code
        ---index.py // indexes Symbols in the repository
        ---models.py // contains dataclasses for Symbols and Chunks
        ---parser.py // parses Symbols and Chunks from the working directory
        ---vector_index.py // applies semantic indexing  and embeddings using FAISS 
    ---knowledge/
        ---docs/
        ---external/
            ---sources.json
            ---<file>.md
        ---indexed/
        ---notes/
    ---models/
        ---/Qwen3-4B-GGUF
            ---Qwen3-4B-Q5_K_M.gguf
    ---retrieval/
        ---context.py // assembles retrieved code chunks into clean context blocks
    ---sandbox/
        ---docker_sandbox.py // sadboxes using docker
        ---Dockerfile
    ---server/
        ---__init__.py
        ---llm.py // creates the llm server using OpenAI api
    ---tests/
        ---test_<name>.py // contains test cases for individual modules [For some cases Error thrown implies a passed test case]
    ---tools/
        ---code_index.py // searches the repositories using code index
        ---filesystem.py // contains file specific commands to read, write, edit
        ---knowledge_index.py // applies FAISS and BAAI BGE embeddings to Knowledge Base
        ---knowledge_ingest.py // wrapper for knowledge_ingestion
        ---knowledge_ingestion.py // contains logic for knowledge ingestion and removal
        ---knowledge_search.py // searches for relevant knowledge sources
        ---registry.py // registry of tools
        ---schemas.py // schema containing metadata about tools used by RuneStones
        ---semantic_search.py // tool for semantic search  
        ---terminal.py // allows terminal commands
    ---agent.py // Contains RuneStone definition
    ---main.py // Contains the entry point of Rune Stone
```

## How to operate:

Operating involves the following requirements:

- Run the following command to start the server:
```
llama-server `
  -m ".\models\Qwen3-4B-GGUF\Qwen3-4B-Q5_K_M.gguf" `
  --alias "qwen3-4b" `
  -ngl 99 `
  --jinja `
  --reasoning off `
  --host 127.0.0.1 `
  --port 8080 `
  -c 8192
  ```

  - Start Docker 
  - Run main.py 
```
    python main.py
```