from indexer.index import index_repository, search_symbols
from indexer.models import CodeSymbol


class CodeIndex:
    def __init__(self, repository_path: str):
        self.repository_path = repository_path
        self.symbols: list[CodeSymbol] = []

    def build(self):
        self.symbols = index_repository(
            self.repository_path
        )

    def search(self, query: str) -> list[CodeSymbol]:
        return search_symbols(
            self.symbols,
            query,
        )

    def summary(self) -> str:
        return (
            f"Repository: {self.repository_path}\n"
            f"Symbols indexed: {len(self.symbols)}"
        )