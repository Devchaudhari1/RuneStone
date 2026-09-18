from tools.knowledge_ingestion import (
    add_knowledge_source,
    refresh_knowledge_source,
    remove_knowledge_source,
)


def ingest_knowledge(url: str) -> str:
    return add_knowledge_source(url)


def refresh_knowledge(url: str) -> str:
    return refresh_knowledge_source(url)


def remove_knowledge(url: str) -> str:
    return remove_knowledge_source(url)