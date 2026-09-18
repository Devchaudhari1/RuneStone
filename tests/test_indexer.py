import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from indexer.code_index import CodeIndex

def main():
    index = CodeIndex(
        "workspace/demo_project"
    )

    index.build()

    print("\n==============================")
    print("Rune Stone CodeIndex")
    print("==============================\n")

    print(index.summary())

    print("\nSearch: Calculator\n")

    results = index.search("Calculator")

    for symbol in results:
        print(
            f"{symbol.symbol_type}: "
            f"{symbol.name}"
        )

        if symbol.parent:
            print(
                f"Parent: {symbol.parent}"
            )

        print(
            f"File: {symbol.file_path}"
        )

        print(
            f"Lines: "
            f"{symbol.start_line}-"
            f"{symbol.end_line}"
        )

        print(f"\n{symbol.source}\n")
        print("------------------------------")


if __name__ == "__main__":
    main()