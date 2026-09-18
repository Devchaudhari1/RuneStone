from indexer.code_index import CodeIndex


_index_cache = {}


def search_code(query: str, repository: str = ".") -> str:
    """
    Search the repository's structural code index.

    Args:
        query: Symbol name, file name, class name,
               function name, or code text to search for.
        repository: Repository path relative to the workspace.

    Returns:
        Matching code symbols and their source.
    """

    key = repository

    if key not in _index_cache:
        index = CodeIndex(
            f"workspace/{repository}"
        )

        index.build()

        _index_cache[key] = index

    index = _index_cache[key]

    results = index.search(query)

    if not results:
        return f"No code found matching: {query}"

    output = []

    for symbol in results[:20]:
        output.append(
            f"TYPE: {symbol.symbol_type}\n"
            f"NAME: {symbol.name}\n"
            f"FILE: {symbol.file_path}\n"
            f"LINES: {symbol.start_line}-{symbol.end_line}\n"
            f"PARENT: {symbol.parent or 'None'}\n"
            f"SOURCE:\n{symbol.source}"
        )

    return "\n\n==============================\n\n".join(
        output
    )