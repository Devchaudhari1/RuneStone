from pathlib import Path

from indexer.vector_index import SemanticCodeIndex
from retrieval.context import assemble_context


_index_cache = {}


def _repository_signature(repository: str) -> int:
    root = Path("workspace") / repository

    if not root.exists():
        return 0

    latest_mtime = 0

    ignored = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        "node_modules",
    }

    for path in root.rglob("*.py"):
        if any(part in ignored for part in path.parts):
            continue

        try:
            latest_mtime = max(
                latest_mtime,
                path.stat().st_mtime_ns,
            )
        except OSError:
            continue

    return latest_mtime


def search_semantic(
    query: str,
    repository: str = ".",
    top_k: int = 5,
) -> str:
    """
    Perform semantic code search and assemble the results
    into clean context for the agent.
    """

    signature = _repository_signature(repository)

    cached = _index_cache.get(repository)

    if cached is None or cached["signature"] != signature:
        print("[Semantic Index] Building / refreshing index...")

        index = SemanticCodeIndex(
            f"workspace/{repository}"
        )

        index.build()

        _index_cache[repository] = {
            "index": index,
            "signature": signature,
        }

    index = _index_cache[repository]["index"]

    results = index.search(
        query,
        top_k=top_k,
    )

    if not results:
        return f"No semantically relevant code found for: {query}"

    output = []

    for result in results:
        chunk = result["chunk"]

        output.append(
            f"DIVERSITY SCORE: "
            f"{result.get('diversity_score', result['score']):.4f}\n"
            f"HYBRID SCORE: "
            f"{result['score']:.4f}\n"
            f"SEMANTIC SCORE: "
            f"{result['semantic_score']:.4f}\n"
            f"LEXICAL SCORE: "
            f"{result['lexical_score']:.4f}\n"
            f"TYPE: {chunk.symbol_type}\n"
            f"NAME: {chunk.symbol_name}\n"
            f"FILE: {chunk.file_path}\n"
            f"LINES: "
            f"{chunk.start_line}-{chunk.end_line}"
        )

    chunks = [
        result["chunk"]
        for result in results
    ]

    context = assemble_context(
        chunks,
        max_chars=12000,
    )

    return (
        "\n\n".join(output)
        + "\n\n"
        + context
    )