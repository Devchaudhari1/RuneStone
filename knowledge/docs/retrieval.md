# Retrieval

RuneStone provides multiple retrieval systems for coding and knowledge tasks.

## Semantic Search

Semantic code search uses the BAAI/bge-small-en-v1.5 embedding model.

Embeddings are stored in a FAISS index for efficient similarity search.

## Hybrid Retrieval

Knowledge retrieval combines semantic similarity with lexical matching.

The current ranking combines semantic and lexical scores, with semantic similarity weighted more heavily.

## Knowledge Sources

The knowledge base supports documentation, notes, and external knowledge.

Documentation is stored under knowledge/docs/.

Notes are stored under knowledge/notes/.

External knowledge is stored under knowledge/external/.

## Persistent Index

The knowledge index stores FAISS vectors and metadata on disk.

A manifest tracks indexed files so the index can automatically rebuild when files are added, modified, or deleted.