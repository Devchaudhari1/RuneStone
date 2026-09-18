from pathlib import Path

from indexer.parser import parse_python_file
from indexer.models import CodeSymbol


IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
}


def index_repository(root_path: str) -> list[CodeSymbol]:
    root = Path(root_path).resolve()

    if not root.exists():
        raise ValueError(
            f"Repository does not exist: {root}"
        )

    if not root.is_dir():
        raise ValueError(
            f"Repository path is not a directory: {root}"
        )

    symbols = []

    for path in root.rglob("*.py"):
        if any(
            ignored in path.parts
            for ignored in IGNORED_DIRECTORIES
        ):
            continue

        symbols.extend(
            parse_python_file(str(path))
        )

    return symbols


def search_symbols(
    symbols: list[CodeSymbol],
    query: str,
) -> list[CodeSymbol]:

    query = query.lower()

    results = []

    for symbol in symbols:
        searchable = " ".join(
            [
                symbol.name,
                symbol.symbol_type,
                symbol.file_path,
                symbol.parent,
                symbol.source,
            ]
        ).lower()

        if query in searchable:
            results.append(symbol)

    return results