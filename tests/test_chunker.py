import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from indexer.index import index_repository
from indexer.chunker import symbols_to_chunks


symbols = index_repository("workspace/demo_project")

chunks = symbols_to_chunks(symbols)

print(f"Symbols: {len(symbols)}")
print(f"Chunks:  {len(chunks)}")

for chunk in chunks[:5]:
    print("\n==============================")
    print(chunk.content)