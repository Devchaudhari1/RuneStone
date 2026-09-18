import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from embeddings.embedder import CodeEmbedder


def main():
    print("Creating embedder 1...")
    e1 = CodeEmbedder()

    print("Creating embedder 2...")
    e2 = CodeEmbedder()

    print("Creating embedder 3...")
    e3 = CodeEmbedder()

    print("\nSame instance:")
    print(e1 is e2)
    print(e2 is e3)


if __name__ == "__main__":
    main()