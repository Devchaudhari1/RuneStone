from tools.knowledge_index import KnowledgeIndex


_index = None


def _get_index() -> KnowledgeIndex:
    global _index

    if _index is None:
        _index = KnowledgeIndex()

    return _index


def search_knowledge(
    query: str,
    top_k: int = 5,
    source_type: str | None = None,
) -> str:
    index = _get_index()

    results = index.search(
        query=query,
        top_k=top_k,
        source_type=source_type,
    )

    if not results:
        return "No relevant knowledge-base results found."

    output = []

    for i, result in enumerate(results, start=1):
        output.append(
            f"[Knowledge Result {i}]\n"
            f"Source: {result['source']}\n"
            f"Type: {result.get('source_type', 'unknown')}\n"
            f"Heading: {result['heading'] or '(none)'}\n"
            f"Lines: {result['start_line']}-{result['end_line']}\n"
            f"Score: {result['score']:.4f}\n"
            f"Semantic: {result['semantic_score']:.4f}\n"
            f"Lexical: {result['lexical_score']:.4f}\n"
            f"\n{result['text']}"
        )

    return "\n\n".join(output)