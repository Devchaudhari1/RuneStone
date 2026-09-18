from indexer.models import CodeChunk


DEFAULT_MAX_CHARS = 12000


def assemble_context(
    chunks: list[CodeChunk],
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Assemble retrieved code chunks into a clean context block.

    The budget is currently measured in characters.
    """

    if not chunks:
        return "No relevant code was found."

    sections = []
    total_chars = 0

    for number, chunk in enumerate(chunks, start=1):
        header = (
            f"[{number}] "
            f"{chunk.file_path}:"
            f"{chunk.start_line}-"
            f"{chunk.end_line}"
        )

        metadata = [
            f"TYPE: {chunk.symbol_type}",
        ]

        if chunk.symbol_name:
            metadata.append(f"SYMBOL: {chunk.symbol_name}")

        if chunk.parent:
            metadata.append(f"PARENT: {chunk.parent}")

        # CodeChunk.content already contains metadata.
        # Remove that metadata so it isn't duplicated.
        source = chunk.content

        if "\n\n" in source:
            source = source.split("\n\n", 1)[1]

        content = (
            f"{header}\n"
            + "\n".join(metadata)
            + "\n\n"
            + source.strip()
        )

        # Don't exceed the context budget.
        if total_chars + len(content) > max_chars:
            break

        sections.append(content)
        total_chars += len(content)

    if not sections:
        return "No relevant code fits within the context budget."

    return (
        "RELEVANT CODE\n"
        "==============\n\n"
        + "\n\n".join(sections)
    )