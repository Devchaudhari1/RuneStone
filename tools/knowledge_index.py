from __future__ import annotations

import re
import json
from pathlib import Path
import os

# RuneStone uses the embedding model locally.
# Prevent Hugging Face Hub network access during normal operation.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_ROOT = PROJECT_ROOT / "knowledge"
INDEX_ROOT = KNOWLEDGE_ROOT / "indexed"

INDEX_FILE = INDEX_ROOT / "knowledge.faiss"
METADATA_FILE = INDEX_ROOT / "metadata.json"
MANIFEST_FILE = INDEX_ROOT / "manifest.json"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

SUPPORTED_EXTENSIONS = {".md", ".txt"}

SOURCE_TYPES = {
    "docs": "documentation",
    "notes": "notes",
    "external": "external",
}

class KnowledgeIndex:
    def __init__(
        self,
        knowledge_root: Path = KNOWLEDGE_ROOT,
        index_root: Path = INDEX_ROOT,
    ):
        self.knowledge_root = Path(knowledge_root)
        self.index_root = Path(index_root)

        self.index_root.mkdir(parents=True, exist_ok=True)

        self.index = None
        self.metadata = []

        if not hasattr(KnowledgeIndex, "_shared_model"):
            KnowledgeIndex._shared_model = SentenceTransformer(
                EMBEDDING_MODEL,
                local_files_only=True,
            )

        self._model = KnowledgeIndex._shared_model

        self._load_existing()

    # ---------------------------------------------------------
    # File discovery
    # ---------------------------------------------------------

    def _discover_files(self) -> list[Path]:
        files = []

        for path in self.knowledge_root.rglob("*"):
            if not path.is_file():
                continue

            if path.parent == self.index_root:
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            files.append(path)

        return sorted(files)

    # ---------------------------------------------------------
    # Manifest
    # ---------------------------------------------------------

    def _build_manifest(self) -> dict:
        files = self._discover_files()

        manifest = {}

        for path in files:
            relative = path.relative_to(self.knowledge_root).as_posix()

            stat = path.stat()

            manifest[relative] = {
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }

        return manifest

    def _load_manifest(self) -> dict | None:
        if not MANIFEST_FILE.exists():
            return None

        try:
            return json.loads(
                MANIFEST_FILE.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return None

    def _save_manifest(self, manifest: dict) -> None:
        MANIFEST_FILE.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def _lexical_score(
        self,
        query: str,
        text: str,
        heading: str = "",
    ) -> float:

        query_terms = set(
            re.findall(
                r"\b[a-zA-Z0-9_+-]+\b",
                query.lower(),
            )
        )

        if not query_terms:
            return 0.0

        text_terms = set(
            re.findall(
                r"\b[a-zA-Z0-9_+-]+\b",
                text.lower(),
            )
        )

        heading_terms = set(
            re.findall(
                r"\b[a-zA-Z0-9_+-]+\b",
                heading.lower(),
            )
        )

        if not text_terms:
            return 0.0

        matched = query_terms & text_terms

        body_score = len(matched) / len(query_terms)

        heading_matches = query_terms & heading_terms

        heading_score = (
            len(heading_matches) / len(query_terms)
        )

        # Heading matches receive a modest boost.
        return min(
            1.0,
            body_score * 0.7 + heading_score * 0.3,
        )
    #----------------------------------------------------------
    # Get Source Type
    #----------------------------------------------------------

    def _get_source_type(self, path: Path) -> str:
        try:
            relative = path.relative_to(self.knowledge_root)
        except ValueError:
            return "unknown"

        if not relative.parts:
            return "unknown"

        top_level = relative.parts[0].lower()

        return SOURCE_TYPES.get(top_level, "unknown")

    # ---------------------------------------------------------
    # Existing index
    # ---------------------------------------------------------

    def _load_existing(self) -> bool:
        if not INDEX_FILE.exists():
            return False

        if not METADATA_FILE.exists():
            return False

        if not MANIFEST_FILE.exists():
            return False

        try:
            self.index = faiss.read_index(str(INDEX_FILE))

            self.metadata = json.loads(
                METADATA_FILE.read_text(
                    encoding="utf-8"
                )
            )

            return True

        except Exception:
            self.index = None
            self.metadata = []
            return False

    # ---------------------------------------------------------
    # Change detection
    # ---------------------------------------------------------

    def needs_rebuild(self) -> bool:
        current_manifest = self._build_manifest()
        previous_manifest = self._load_manifest()

        if previous_manifest is None:
            return True

        return current_manifest != previous_manifest

    # ---------------------------------------------------------
    # Markdown parsing
    # ---------------------------------------------------------

    def _chunk_document(
        self,
        path: Path,
        max_chars: int = 1800,
    ) -> list[dict]:

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        chunks = []

        current_heading = ""
        current_lines = []
        start_line = 1

        def flush(end_line: int):
            nonlocal current_lines, start_line

            if not current_lines:
                return

            chunk_text = "\n".join(current_lines).strip()

            if not chunk_text:
                return

            relative = path.relative_to(
                self.knowledge_root
            ).as_posix()

            chunks.append(
                {
                    "source": relative,
                    "type": "knowledge",
                    "source_type": self._get_source_type(path),
                    "heading": current_heading,
                    "start_line": start_line,
                    "end_line": end_line,
                    "text": chunk_text,
                }
            )

            current_lines = []

        for line_number, line in enumerate(
            lines,
            start=1,
        ):
            if line.startswith("#"):
                flush(line_number - 1)

                current_heading = line.lstrip("#").strip()
                start_line = line_number
                current_lines = [line]

                continue

            current_lines.append(line)

            current_text = "\n".join(current_lines)

            if len(current_text) >= max_chars:
                flush(line_number)

                start_line = line_number + 1

        flush(len(lines))

        return chunks

    # ---------------------------------------------------------
    # Build
    # ---------------------------------------------------------

    def build(self) -> int:
        files = self._discover_files()

        chunks = []

        for path in files:
            try:
                chunks.extend(
                    self._chunk_document(path)
                )
            except UnicodeDecodeError:
                print(
                    f"[Knowledge] Skipping non-UTF8 file: {path}"
                )

        if not chunks:
            dimension = self._model.get_sentence_embedding_dimension()

            self.index = faiss.IndexFlatIP(dimension)
            self.metadata = []

        else:
            texts = [
                chunk["text"]
                for chunk in chunks
            ]

            embeddings = self._model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            embeddings = np.asarray(
                embeddings,
                dtype=np.float32,
            )

            dimension = embeddings.shape[1]

            self.index = faiss.IndexFlatIP(
                dimension
            )

            self.index.add(embeddings)

            self.metadata = chunks

        current_manifest = self._build_manifest()

        faiss.write_index(
            self.index,
            str(INDEX_FILE),
        )

        METADATA_FILE.write_text(
            json.dumps(
                self.metadata,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self._save_manifest(
            current_manifest
        )

        print(
            f"[Knowledge] Built index: "
            f"{len(chunks)} chunks from "
            f"{len(files)} files."
        )

        return len(chunks)

    # ---------------------------------------------------------
    # Ensure current
    # ---------------------------------------------------------

    def ensure_current(self) -> None:
        if self.index is None:
            print(
                "[Knowledge] No existing index. Building..."
            )

            self.build()
            return

        if self.needs_rebuild():
            print(
                "[Knowledge] Knowledge base changed. "
                "Rebuilding index..."
            )

            self.build()

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
    ) -> list[dict]:

        self.ensure_current()

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        if top_k <= 0:
            return []

        query_embedding = self._model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32,
        )
        if source_type is not None:
            valid_source_types = {
                "documentation",
                "notes",
                "external",
            }

            if source_type not in valid_source_types:
                raise ValueError(
                    f"Invalid source_type: {source_type}. "
                    f"Expected one of: {sorted(valid_source_types)}"
                )
        # Retrieve more candidates than requested so that
        # source filtering does not accidentally remove
        # relevant results.
        if source_type is not None:
            candidate_k = min(
                max(top_k * 10, 50),
                self.index.ntotal,
            )
        else:
            candidate_k = min(
                top_k,
                self.index.ntotal,
            )

        scores, indices = self.index.search(
            query_embedding,
            candidate_k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            result = dict(
                self.metadata[index]
            )

            if (
                source_type is not None
                and result.get("source_type") != source_type
            ):
                continue

            semantic_score = float(score)

            lexical_score = self._lexical_score(
                query=query,
                text=result["text"],
                heading=result.get("heading", ""),
            )

            final_score = (
                semantic_score * 0.75
                + lexical_score * 0.25
            )

            result["semantic_score"] = semantic_score
            result["lexical_score"] = lexical_score
            result["score"] = final_score

            results.append(result)

            if len(results) >= top_k:
                break
        results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return results[:top_k]
    
        return results