from pathlib import Path

from indexer.models import CodeSymbol, CodeChunk


def symbol_to_chunk(symbol: CodeSymbol) -> CodeChunk:
    """Convert a parsed code symbol into a contextual retrieval chunk."""

    context_parts = [
        f"FILE: {symbol.file_path}",
        f"TYPE: {symbol.symbol_type}",
    ]

    if symbol.parent:
        context_parts.append(f"PARENT: {symbol.parent}")

    if symbol.name:
        context_parts.append(f"SYMBOL: {symbol.name}")

    context_parts.append("")
    context_parts.append(symbol.source)

    content = "\n".join(context_parts)

    return CodeChunk(
        content=content,
        file_path=symbol.file_path,
        start_line=symbol.start_line,
        end_line=symbol.end_line,
        symbol_name=symbol.name,
        symbol_type=symbol.symbol_type,
        parent=symbol.parent,
    )


def symbols_to_chunks(symbols: list[CodeSymbol]) -> list[CodeChunk]:
    """Convert parsed symbols into symbol-level retrieval chunks."""

    return [
        symbol_to_chunk(symbol)
        for symbol in symbols
    ]


def file_to_context_chunk(file_path: str) -> CodeChunk | None:
    """
    Create one contextual chunk representing an entire source file.
    """

    path = Path(file_path)

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not source.strip():
        return None

    lines = source.splitlines()

    content = "\n".join(
        [
            f"FILE: {path}",
            "TYPE: file_context",
            "",
            source,
        ]
    )

    return CodeChunk(
        content=content,
        file_path=str(path),
        start_line=1,
        end_line=len(lines),
        symbol_name=path.name,
        symbol_type="file_context",
        parent="",
    )


def files_to_context_chunks(
    file_paths: list[str],
) -> list[CodeChunk]:
    """Create contextual chunks for source files."""

    chunks = []

    for file_path in file_paths:
        chunk = file_to_context_chunk(file_path)

        if chunk is not None:
            chunks.append(chunk)

    return chunks