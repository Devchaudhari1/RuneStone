from pathlib import Path
from sentence_transformers import SentenceTransformer


class CodeEmbedder:
    _instance = None

    def __new__(cls, model_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self, model_path=None):
        if self._initialized:
            return

        if model_path is None:
            model_path = (
                Path.home()
                / ".cache"
                / "huggingface"
                / "hub"
                / "models--BAAI--bge-small-en-v1.5"
                / "snapshots"
            )

            snapshots = list(model_path.iterdir())

            if not snapshots:
                raise RuntimeError(
                    "BGE embedding model is not cached locally."
                )

            model_path = snapshots[0]

        model_path = str(model_path)

        print(f"[Embedder] Loading local model: {model_path}")

        self.model = SentenceTransformer(
            model_path,
            local_files_only=True,
        )

        self._initialized = True

    def embed(self, texts: list[str]):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def embed_one(self, text: str):
        return self.embed([text])[0]