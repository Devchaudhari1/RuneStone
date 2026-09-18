import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from indexer.index import index_repository
from indexer.chunker import symbols_to_chunks
from retrieval.context import assemble_context


symbols = index_repository(
    "workspace/demo_project"
)

chunks = symbols_to_chunks(symbols)

context = assemble_context(
    chunks[:5],
    max_chars=5000,
)

print(context)