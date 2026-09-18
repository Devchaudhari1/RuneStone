import faiss
import numpy as np

from indexer.index import index_repository
from indexer.chunker import (
    symbols_to_chunks,
    files_to_context_chunks,
)
from indexer.models import CodeChunk
from embeddings.embedder import CodeEmbedder


class SemanticCodeIndex:

    def __init__(self, repository_path: str):
        self.repository_path = repository_path
        self.embedder = CodeEmbedder()

        self.chunks: list[CodeChunk] = []
        self.index = None

    def build(self):
        print("Building structural code index...")

        symbols = index_repository(self.repository_path)

        print(f"Found {len(symbols)} code symbols.")

        symbol_chunks = symbols_to_chunks(symbols)

        # Find Python source files represented by the repository.
        file_paths = sorted(
            {
                symbol.file_path
                for symbol in symbols
            }
        )

        context_chunks = files_to_context_chunks(file_paths)

        print(
            f"Created {len(symbol_chunks)} symbol chunks."
        )

        print(
            f"Created {len(context_chunks)} file context chunks."
        )

        self.chunks = (
            symbol_chunks +
            context_chunks
        )

        if not self.chunks:
            print("No code chunks found.")
            return

        texts = [
            chunk.content
            for chunk in self.chunks
        ]

        print(
            f"Embedding {len(texts)} total chunks..."
        )

        vectors = self.embedder.embed(texts)

        vectors = np.asarray(
            vectors,
            dtype="float32",
        )

        dimension = vectors.shape[1]

        self.index = faiss.IndexFlatIP(dimension)

        self.index.add(vectors)

        print(
            f"Vector index built: "
            f"{len(self.chunks)} vectors"
        )
    def search(self, query: str, top_k: int = 5):
        if self.index is None:
            return []

        query_vector = self.embedder.embed_one(query)

        query_vector = np.asarray(
            [query_vector],
            dtype="float32",
        )

        # Retrieve a larger candidate pool first.
        candidate_k = min(
            max(top_k * 4, 20),
            len(self.chunks),
        )

        scores, indices = self.index.search(
            query_vector,
            candidate_k,
        )

        query_lower = query.lower()
        query_words = set(query_lower.split())

        candidates = []

        for semantic_score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            chunk = self.chunks[index]

            name = chunk.symbol_name.lower()
            parent = chunk.parent.lower()
            symbol_type = chunk.symbol_type.lower()
            source = chunk.content.lower()

            lexical_score = 0.0

            if name == query_lower:
                lexical_score += 1.0

            elif name and name in query_lower:
                lexical_score += 0.7

            if name in query_words:
                lexical_score += 0.5

            if parent and parent in query_lower:
                lexical_score += 0.3

            if symbol_type in query_lower:
                lexical_score += 0.15

            if query_lower in source:
                lexical_score += 0.2

            hybrid_score = (
                0.80 * float(semantic_score)
                + 0.20 * lexical_score
            )

            candidates.append(
                {
                    "index": index,
                    "score": hybrid_score,
                    "semantic_score": float(semantic_score),
                    "lexical_score": lexical_score,
                    "chunk": chunk,
                }
            )

        # Sort by initial relevance.
        candidates.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        selected = []

        # Maximum number of results.
        remaining = candidates.copy()

        while remaining and len(selected) < top_k:

            best_candidate = None
            best_score = float("-inf")

            for candidate in remaining:

                relevance = candidate["score"]

                # Penalize only strongly redundant chunks.
                redundancy = 0.0

                candidate_chunk = candidate["chunk"]

                for selected_candidate in selected:
                    selected_chunk = selected_candidate["chunk"]

                    # Same exact symbol + same file = essentially duplicate.
                    if (
                        candidate_chunk.file_path
                        == selected_chunk.file_path
                        and candidate_chunk.symbol_name
                        == selected_chunk.symbol_name
                        and candidate_chunk.symbol_type
                        == selected_chunk.symbol_type
                    ):
                        redundancy += 0.35

                    # File-context chunks duplicate specific symbols from
                    # the same file, so give them a moderate penalty.
                    elif (
                        candidate_chunk.symbol_type == "file_context"
                        and candidate_chunk.file_path
                        == selected_chunk.file_path
                        and selected_chunk.symbol_type != "file_context"
                    ):
                        redundancy += 0.20

                    # Two file-context chunks from the same file are duplicates.
                    elif (
                        candidate_chunk.symbol_type == "file_context"
                        and selected_chunk.symbol_type == "file_context"
                        and candidate_chunk.file_path
                        == selected_chunk.file_path
                    ):
                        redundancy += 0.35

                diversity_score = relevance - redundancy

                if diversity_score > best_score:
                    best_score = diversity_score
                    best_candidate = candidate

            if best_candidate is None:
                break

            best_candidate["diversity_score"] = best_score

            selected.append(best_candidate)
            remaining.remove(best_candidate)

        return selected